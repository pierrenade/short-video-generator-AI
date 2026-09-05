from threading import Thread
import time, os, sys
from binance import ThreadedWebsocketManager
from binance.client import Client
from binance.enums import (
    SIDE_SELL, SIDE_BUY,
    FUTURE_ORDER_TYPE_MARKET, FUTURE_ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC, FUTURE_ORDER_TYPE_STOP_MARKET,
    FUTURE_ORDER_TYPE_TAKE_PROFIT
)
from tabulate import tabulate

import TradingStrats
from LiveTradingConfig import *
from Helper import Trade
from Logger import *

def calculate_custom_tp_sl(options):
    """Custom TP/SL that needs trade info; used when TP_SL_choice requires context."""
    sl = tp = -99
    if TP_SL_choice == 'USDT':
        sl, tp = TradingStrats.USDT_SL_TP(options)
    return sl, tp

class TradeManager:
    def __init__(self, client: Client, new_trades_q, print_trades_q):
        self.client = client
        self.active_trades: list[Trade] = []
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_callback = trailing_stop_callback
        self.use_market_orders = use_market_orders
        self.new_trades_q = new_trades_q
        self.print_trades_q = print_trades_q
        self.total_profit = 0
        self.number_of_wins = 0
        self.number_of_losses = 0

        Thread(target=self.check_threshold_loop, daemon=True).start()
        self.twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
        self.twm.start()
        self.user_socket = self.twm.start_futures_user_socket(callback=self.monitor_trades)
        Thread(target=self.log_trades_loop, daemon=True).start()
        Thread(target=self.monitor_orders_by_polling_api, daemon=True).start()

    def monitor_orders_by_polling_api(self):
        """Poll open positions to attach TP/SL when fills happen during packet loss."""
        while True:
            time.sleep(15)
            opens = self.get_all_open_positions()
            if not opens: continue
            try:
                for t in self.active_trades:
                    if t.symbol in opens and t.trade_status == 0:
                        i = self.active_trades.index(t)
                        t.trade_status = self.place_tp_sl(t.symbol, t.trade_direction, t.CP, t.tick_size, t.entry_price, i)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'monitor_orders_by_polling_api() - Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')

    def new_trades_loop(self):
        """Process new trade signals and open orders."""
        while True:
            symbol, OP, CP, tick, direction, _, sl, tp = self.new_trades_q.get()
            open_syms = self.get_all_open_or_pending_trades()
            if open_syms != -1 and symbol not in open_syms and len(self.active_trades) < max_number_of_positions and self.check_margin_sufficient():
                try:
                    order_id, qty, entry, status = self.open_trade(symbol, direction, OP, tick)
                    if TP_SL_choice in custom_tp_sl_functions and status != -1:
                        sl, tp = calculate_custom_tp_sl({'position_size': qty})
                    if status != -1:
                        self.active_trades.append(Trade(0, entry, qty, tp, sl, direction, order_id, symbol, CP, tick))
                    if status == 1:
                        self.active_trades[-1].trade_status = self.place_tp_sl(symbol, direction, CP, tick, entry, -1)
                    elif status == 0:
                        log.info(f'new_trades_loop() - Order placed {symbol}, Entry: {entry}, Qty: {qty}, Side: {"Long" if direction else "Short"}')
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.warning(f'new_trades_loop() - Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')

    def monitor_trades(self, msg):
        """User-stream callback: set TP/SL on fills and track wins/losses/closures."""
        try:
            updates = []
            for t in self.active_trades:
                if msg['e'] == 'ORDER_TRADE_UPDATE' and msg['o']['s'] == t.symbol and msg['o']['X'] == 'FILLED':
                    i = self.active_trades.index(t)
                    rp = float(msg['o']['rp'])
                    oid = msg['o']['i']
                    if rp > 0 and oid == t.TP_id:
                        self.total_profit += rp; self.number_of_wins += 1; updates.append([i, 4])
                    elif rp < 0 and oid == t.SL_id:
                        self.total_profit += rp; self.number_of_losses += 1; updates.append([i, 5])
                    elif oid == t.order_id:
                        status = self.place_tp_sl(t.symbol, t.trade_direction, t.CP, t.tick_size, t.entry_price, i)
                        updates.append([i, status])
                elif msg['e'] == 'ACCOUNT_UPDATE':
                    i = self.active_trades.index(t)
                    for p in msg['a']['P']:
                        if p['s'] == t.symbol and p['pa'] == '0':
                            updates.append([i, 6])
            for i, status in updates:
                self.active_trades[i].trade_status = status
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.warning(f'monitor_trades() - Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')

    def place_tp_sl(self, symbol, direction, CP, tick, entry_price, index):
        """Place TP and SL orders for an opened position."""
        try: self.client.futures_cancel_all_open_orders(symbol=symbol)
        except: pass
        self.active_trades[index].position_size = abs(next(float(p['positionAmt']) for p in self.client.futures_position_information() if p['symbol'] == symbol))
        self.active_trades[index].SL_id = self.place_SL(symbol, self.active_trades[index].SL_val, direction, CP, tick, self.active_trades[index].position_size)
        self.active_trades[index].TP_id = self.place_TP(symbol, [self.active_trades[index].TP_val, self.active_trades[index].position_size], direction, CP, tick)
        if self.active_trades[index].SL_id != -1 and self.active_trades[index].TP_id != -1:
            log.info(f'new_trades_loop() - Position OPEN {symbol}, orderId: {self.active_trades[-1].order_id}, Entry: {entry_price}, Qty: {self.active_trades[index].position_size}, Side: {"Long" if direction else "Short"} | TP & SL placed')
            self.print_trades_q.put(True)
            return 1
        return 3

    def get_all_open_or_pending_trades(self):
        """Symbols with open positions or pending/active bot trades."""
        try:
            opens = [p['symbol'] for p in self.client.futures_position_information() if float(p['notional']) != 0.0]
            actives = [t.symbol for t in self.active_trades]
            return opens + actives
        except Exception as e:
            log.warning(f'get_all_open_or_pending_trades() - {e}')
            return -1

    def get_all_open_positions(self):
        """Symbols with non-zero notional."""
        try:
            return [p['symbol'] for p in self.client.futures_position_information() if float(p['notional']) != 0.0]
        except Exception as e:
            log.warning(f'get_all_open_trades() - {e}')
            return []

    def check_margin_sufficient(self):
        """Ensure margin is sufficient before opening a new position."""
        try:
            a = self.client.futures_account()
            return float(a['totalMarginBalance']) > (float(a['totalWalletBalance']) * (1 - order_size / 100)) / leverage
        except Exception as e:
            log.warning(f'check_margin_sufficient() - {e}')
            return False

    def check_threshold_loop(self):
        """Cancel stale entries when price has moved beyond configured threshold."""
        while True:
            try:
                time.sleep(5)
                for t in self.active_trades:
                    if t.trade_status == 0:
                        px = float(self.client.futures_symbol_ticker(symbol=t.symbol)['price'])
                        moved = (px - t.entry_price) / t.entry_price if t.trade_direction == 1 else (t.entry_price - px) / t.entry_price
                        if moved > trading_threshold / 100:
                            t.current_price = px; t.trade_status = 2
                self.cancel_and_remove_trades()
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'check_threshold_loop() - Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')

    def cancel_and_remove_trades(self):
        """Remove finished/failed trades from active list and clean orders."""
        i = 0
        opens = self.get_all_open_positions()
        while i < len(self.active_trades):
            t = self.active_trades[i]
            try:
                if t.trade_status == 2 and opens:
                    if self.check_position_and_cancel_orders(t, opens):
                        pct = abs(100 * (t.entry_price - t.current_price) / t.entry_price)
                        log.info(f'cancel_and_remove_trades() - Cancelled {t.symbol} (threshold exceeded). Current: {t.current_price}, Entry: {t.entry_price}, Δ%: {pct}')
                        self.active_trades.pop(i); continue
                    t.trade_status = 0; i += 1
                elif t.trade_status == 3:
                    self.close_position(t.symbol, t.trade_direction, t.position_size)
                    log.info(f'cancel_and_remove_trades() - Cancelled {t.symbol} due to TP/SL placement issue')
                    self.active_trades.pop(i)
                elif t.trade_status in (4,5,6):
                    self.client.futures_cancel_all_open_orders(symbol=t.symbol)
                    reason = {4:"TP hit",5:"SL hit",6:"Position closed"}[t.trade_status]
                    log.info(f'cancel_and_remove_trades() - Closed {t.symbol}: {reason}')
                    self.active_trades.pop(i)
                else:
                    i += 1
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'cancel_and_remove_trades() - {t.symbol} | Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')
                i += 1

    def open_trade(self, symbol, direction, OP, tick):
        """Submit market/limit entry and return (order_id, qty, entry_price, status)."""
        try:
            ob = self.client.futures_order_book(symbol=symbol)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.warning(f'open_trade() - Order book error | Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')
            return -1, -1, -1, -1

        entry_price = float(ob['bids'][0][0]) if direction == 1 else float(ob['asks'][0][0])
        bal = self.get_account_balance()
        notional = leverage * bal * (order_size / 100)
        qty = round(notional / entry_price) if OP == 0 else round(notional / entry_price, OP)

        if self.use_market_orders:
            try:
                side = SIDE_SELL if direction == 0 else SIDE_BUY
                order = self.client.futures_create_order(symbol=symbol, side=side, type=FUTURE_ORDER_TYPE_MARKET, quantity=qty)
                oid = order['orderId']
                mkt_entry = float(self.client.futures_position_information(symbol=symbol)[0]['entryPrice'])
                return oid, qty, mkt_entry, 1
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'open_trade() - Market order error {symbol}, OP:{OP}, dir:{direction}, qty:{qty} | Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')
                return -1, -1, -1, -1
        else:
            try:
                side = SIDE_SELL if direction == 0 else SIDE_BUY
                order = self.client.futures_create_order(symbol=symbol, side=side, type=FUTURE_ORDER_TYPE_LIMIT, price=entry_price, timeInForce=TIME_IN_FORCE_GTC, quantity=qty)
                return order['orderId'], qty, entry_price, 0
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'open_trade() - Limit order error {symbol}, OP:{OP}, tick:{tick}, entry:{entry_price}, dir:{direction}, qty:{qty} | Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')
                return -1, -1, -1, -1

    def get_account_balance(self):
        """Return USDT futures balance."""
        try:
            for x in self.client.futures_account_balance():
                if x['asset'] == 'USDT': return float(x['balance'])
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.warning(f'get_account_balance() - Info: {(exc_obj, fname, exc_tb.tb_lineno)}, Error: {e}')

    def place_TP(self, symbol, TP, direction, CP, tick):
        """Place a Take Profit (or trailing) order."""
        try:
            tp_val = round(TP[0]) if CP == 0 else round(round(TP[0] / tick) * tick, CP)
            side = SIDE_SELL if direction == 1 else SIDE_BUY
            if not self.use_trailing_stop:
                o = self.client.futures_create_order(symbol=symbol, side=side, type=FUTURE_ORDER_TYPE_TAKE_PROFIT, price=tp_val, stopPrice=tp_val, timeInForce=TIME_IN_FORCE_GTC, reduceOnly='true', quantity=TP[1])
            else:
                o = self.client.futures_create_order(symbol=symbol, side=side, type='TRAILING_STOP_MARKET', ActivationPrice=tp_val, callbackRate=self.trailing_stop_callback, quantity=TP[1])
            return o['orderId']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.warning(f"place_TP() - {symbol} price:{tp_val}, qty:{TP[1]} | Error: {e}, Info: {(exc_type, fname, exc_tb.tb_lineno)}")
            return -1

    def place_SL(self, symbol, SL, direction, CP, tick, qty):
        """Place a Stop Loss order."""
        try:
            SL = round(SL) if CP == 0 else round(round(SL / tick) * tick, CP)
            side = SIDE_SELL if direction == 1 else SIDE_BUY
            o = self.client.futures_create_order(symbol=symbol, side=side, type=FUTURE_ORDER_TYPE_STOP_MARKET, reduceOnly='true', stopPrice=SL, quantity=qty)
            return o['orderId']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.warning(f"place_SL() - {symbol} price:{SL} | Error: {e}, Info: {(exc_type, fname, exc_tb.tb_lineno)}")
            return -1

    def close_position(self, symbol, direction, qty):
        """Force-close an open position (used on errors/conditions)."""
        try:
            self.client.futures_cancel_all_open_orders(symbol=symbol)
        except:
            log.warning(f'close_position() - Could not cancel open orders for {symbol} (maybe none)')
        side = SIDE_BUY if direction == 0 else SIDE_SELL
        self.client.futures_create_order(symbol=symbol, side=side, type=FUTURE_ORDER_TYPE_MARKET, quantity=qty)

    def check_position_and_cancel_orders(self, trade: Trade, open_trades: list[str]):
        """Cancel orders only if no position has been entered."""
        if trade.symbol not in open_trades:
            self.client.futures_cancel_all_open_orders(symbol=trade.symbol)
            return True
        return False

    def log_trades_loop(self):
        """Continuously print account/trade summary when updates arrive."""
        while True:
            try:
                self.print_trades_q.get()
                positions = [p for p in self.client.futures_position_information() if float(p['notional']) != 0.0]
                win_loss = 'Not available yet'
                if self.number_of_losses: win_loss = round(self.number_of_wins / self.number_of_losses, 4)
                if positions:
                    info = {'Symbol': [], 'Position Size': [], 'Direction': [], 'Entry Price': [], 'Market Price': [], 'TP': [], 'SL': [], 'Distance to TP (%)': [], 'Distance to SL (%)': [], 'PNL': []}
                    orders = self.client.futures_get_open_orders()
                    tps = {f'{o["symbol"]}_TP': float(o['price']) for o in orders if o.get('reduceOnly') is True and o['type'] == 'TAKE_PROFIT'}
                    sls = {f'{o["symbol"]}_SL': float(o['stopPrice']) for o in orders if o['origType'] == 'STOP_MARKET'}
                    open_orders = {**tps, **sls}
                    for p in positions:
                        sym = p['symbol']; mp = float(p['markPrice']); ep = p['entryPrice']
                        info['Symbol'].append(sym)
                        info['Position Size'].append(p['positionAmt'])
                        info['Direction'].append('LONG' if float(p['notional']) > 0 else 'SHORT')
                        info['Entry Price'].append(ep)
                        info['Market Price'].append(p['markPrice'])
                        tpv = open_orders.get(f'{sym}_TP'); slv = open_orders.get(f'{sym}_SL')
                        info['TP'].append(tpv if tpv is not None else 'Not opened yet')
                        info['SL'].append(slv if slv is not None else 'Not opened yet')
                        info['Distance to TP (%)'].append(round(abs((mp - tpv) / mp * 100), 3) if tpv else 'Not available yet')
                        info['Distance to SL (%)'].append(round(abs((mp - slv) / mp * 100), 3) if slv else 'Not available yet')
                        info['PNL'].append(float(p['unRealizedProfit']))
                    log.info(f'Balance: ${round(self.get_account_balance() or 0, 3)}, Total PnL: ${round(self.total_profit, 3)}, Unrealized: ${round(sum(info["PNL"]),3)}, Wins: {self.number_of_wins}, Losses: {self.number_of_losses}, W/L: {win_loss}, Open: {len(info["Symbol"])}\n' + tabulate(info, headers='keys', tablefmt='github'))
                else:
                    log.info(f'Balance: ${round(self.get_account_balance() or 0, 3)}, Total PnL: ${round(self.total_profit, 3)}, Wins: {self.number_of_wins}, Losses: {self.number_of_losses}, W/L: {win_loss}, No Open Positions')
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info(); fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.warning(f'log_trades_loop() - {e}, Info: {(exc_type, fname, exc_tb.tb_lineno)}')

def start_new_trades_loop_multiprocess(client: Client, new_trades_q, print_trades_q):
    TM = TradeManager(client, new_trades_q, print_trades_q)
    TM.new_trades_loop()
