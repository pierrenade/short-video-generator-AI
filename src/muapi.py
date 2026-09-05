import random
import re

existing_versions = {
    116: [
        '116.0.5845.172',
        '116.0.5845.164',
        '116.0.5845.163',
        '116.0.5845.114',
        '116.0.5845.92'
    ],
    117: [
        '117.0.5938.154',
        '117.0.5938.141',
        '117.0.5938.140',
        '117.0.5938.61',
        '117.0.5938.61',
        '117.0.5938.60'
    ],
    118: [
        '118.0.5993.112',
        '118.0.5993.111',
        '118.0.5993.80',
        '118.0.5993.65',
        '118.0.5993.48'
    ],
    119: [
        '119.0.6045.194',
        '119.0.6045.193',
        '119.0.6045.164',
        '119.0.6045.163',
        '119.0.6045.134',
        '119.0.6045.134',
        '119.0.6045.66',
        '119.0.6045.53'
    ],
    120: [
        '120.0.6099.230',
        '120.0.6099.210',
        '120.0.6099.194',
        '120.0.6099.193',
        '120.0.6099.145',
        '120.0.6099.144',
        '120.0.6099.144',
        '120.0.6099.116',
        '120.0.6099.116',
        '120.0.6099.115',
        '120.0.6099.44',
        '120.0.6099.43'
    ],
    121: [
        '121.0.6167.178',
        '121.0.6167.165',
        '121.0.6167.164',
        '121.0.6167.164',
        '121.0.6167.144',
        '121.0.6167.143',
        '121.0.6167.101'
    ],
    122: [
        '122.0.6261.119',
        '122.0.6261.106',
        '122.0.6261.105',
        '122.0.6261.91',
        '122.0.6261.90',
        '122.0.6261.64',
        '122.0.6261.43'
    ],
    123: [
        '123.0.6312.121',
        '123.0.6312.120',
        '123.0.6312.119',
        '123.0.6312.118',
        '123.0.6312.99',
        '123.0.6312.80',
        '123.0.6312.41',
        '123.0.6312.40'
    ],
    124: [
        '124.0.6367.179',
        '124.0.6367.172',
        '124.0.6367.171',
        '124.0.6367.114',
        '124.0.6367.113',
        '124.0.6367.83',
        '124.0.6367.82',
        '124.0.6367.54'
    ],
    125: [
        '125.0.6422.165',
        '125.0.6422.164',
        '125.0.6422.147',
        '125.0.6422.146',
        '125.0.6422.113',
        '125.0.6422.72',
        '125.0.6422.72',
        '125.0.6422.53',
        '125.0.6422.52'
    ],
    126: [
        '126.0.6478.122',
        '126.0.6478.72',
        '126.0.6478.71',
        '126.0.6478.50'
    ],
    130: [
        "130.0.6669.0",
        "130.0.6669.1",
        "130.0.6669.2",
        "130.0.6670.0",
        "130.0.6674.2",
        "130.0.6675.0",
        "130.0.6675.1",
        "130.0.6676.0",
        "130.0.6676.1",
        "130.0.6677.0",
        "130.0.6677.1",
        "130.0.6677.2",
        "130.0.6678.0",
        "130.0.6678.1",
        "130.0.6679.0",
        "130.0.6679.1",
        "130.0.6679.2",
        "130.0.6679.3",
        "130.0.6680.0",
        "130.0.6680.1",
        "130.0.6680.2",
        "130.0.6681.0",
        "130.0.6681.1",
        "130.0.6682.0",
        "130.0.6682.1",
        "130.0.6682.2",
        "130.0.6682.3",
        "130.0.6683.0",
        "130.0.6683.1",
        "130.0.6683.2",
        "130.0.6683.3"
    ],
    131: [
        "131.0.6724.0",
        "131.0.6724.1",
        "131.0.6724.2",
        "131.0.6725.0",
        "131.0.6725.1",
        "131.0.6725.2",
        "131.0.6725.3",
        "131.0.6726.0",
        "131.0.6726.1",
        "131.0.6726.2",
        "131.0.6727.0",
        "131.0.6727.1",
        "131.0.6728.0",
        "131.0.6728.1",
        "131.0.6729.0",
        "131.0.6729.1",
        "131.0.6730.0",
        "131.0.6730.1",
        "131.0.6731.0",
        "131.0.6731.1",
        "131.0.6732.0",
        "131.0.6732.1",
        "131.0.6733.0",
        "131.0.6733.1",
        "131.0.6734.0"
    ],
    132: [
        "132.0.6779.0",
        "132.0.6779.1",
        "132.0.6780.0",
        "132.0.6780.1",
        "132.0.6781.0",
        "132.0.6781.1",
        "132.0.6782.0",
        "132.0.6782.1",
        "132.0.6783.0",
        "132.0.6783.1",
        "132.0.6784.0",
        "132.0.6784.1",
        "132.0.6784.2",
        "132.0.6785.0",
        "132.0.6785.1",
        "132.0.6786.0",
        "132.0.6786.1",
        "132.0.6787.0",
        "132.0.6787.1",
        "132.0.6788.0",
        "132.0.6788.1",
        "132.0.6789.0",
        "132.0.6789.1",
        "132.0.6789.2",
        "132.0.6790.0",
        "132.0.6790.1",
        "132.0.6790.2"
    ],
    133: [
        "133.0.6835.0",
        "133.0.6835.1",
        "133.0.6835.2",
        "133.0.6835.3",
        "133.0.6835.4",
        "133.0.6836.0",
        "133.0.6836.1",
        "133.0.6837.0",
        "133.0.6837.1",
        "133.0.6838.0",
        "133.0.6838.1",
        "133.0.6839.0",
        "133.0.6839.1",
        "133.0.6840.0",
        "133.0.6840.1",
        "133.0.6841.0",
        "133.0.6841.1"
    ]
}

android_versions = ['10', '11', '12', '13', '14', '15']
android_sdks = {
    '10': '29',
    '11': '30',
    '12': '32',
    '13': '33',
    '14': '34',
    '15': '35'
}
manufacturers = ['Samsung', 'Google', 'OnePlus', 'Xiaomi']

android_devices = {
    'Samsung': [
        'SM-G960F', 'SM-G973F', 'SM-G980F', 'SM-G960U', 'SM-G973U', 'SM-G980U',
        'SM-A505F', 'SM-A515F', 'SM-A525F', 'SM-N975F', 'SM-N986B', 'SM-N981B',
        'SM-F711B', 'SM-F916B', 'SM-G781B', 'SM-G998B', 'SM-G991B', 'SM-G996B',
        'SM-G990E', 'SM-G990B2', 'SM-G990U', 'SM-G990B', 'SM-G990', 'SM-S911B'
    ],
    'Google': [
        'Pixel 2', 'Pixel 2 XL', 'Pixel 3', 'Pixel 3 XL', 'Pixel 4', 'Pixel 4 XL',
        'Pixel 4a', 'Pixel 5', 'Pixel 5a', 'Pixel 5 XL', 'Pixel 6', 'Pixel 6 Pro',
        'Pixel 6 XL', 'Pixel 6a', 'Pixel 7', 'Pixel 7 Pro'
    ],
    'OnePlus': [
        'IN2010', 'IN2023', 'LE2117', 'LE2123', 'CPH2493', 'NE2213'
        'OnePlus Nord', 'IV2201', 'NE2215', 'CPH2423', 'NE2210', 'CPH2419'
    ],
    'Xiaomi': [
        'Mi 9', 'Mi 10', 'Mi 11', 'Mi 12', 'Redmi Note 8',
        'Redmi Note 9', 'Redmi Note 9 Pro', 'Redmi Note 10',
        'Redmi Note 10 Pro', 'Redmi Note 11', 'Redmi Note 11 Pro', 'Redmi Note 12'
    ]}

telegram_versions = [
    '11.0.1', '11.1.0', '11.1.1', '11.1.2', '11.1.3',
    '11.2.0', '11.2.1', '11.2.2', '11.2.3', '11.3.0', '11.3.1',
    '11.3.2', '11.3.3', '11.3.4', '11.4.0', '11.4.2'
]

performance_class = ['AVERAGE', 'HIGH']


def generate_random_user_agent(device_type='android', browser_type='chrome'):
    firefox_versions = list(range(100, 127))  # Last 10 versions of Firefox

    if browser_type == 'chrome':
        major_version = random.choice(list(existing_versions.keys()))
        browser_version = random.choice(existing_versions[major_version])
    elif browser_type == 'firefox':
        browser_version = random.choice(firefox_versions)

    if device_type == 'android':
        android_manufacturer = random.choice(manufacturers)
        android_device = random.choice(android_devices[android_manufacturer])
        android_version = random.choice(android_versions)
        telegram_version = random.choice(telegram_versions)
        performance_version = random.choice(performance_class)
        if browser_type == 'chrome':
            return (
                f"Mozilla/5.0 (Linux; Android {android_version}; {random.choice([android_device, 'K'])}) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{browser_version} Mobile Safari/537.36 Telegram-Android/{telegram_version} "
                f"({android_manufacturer} {android_device}; Android {android_version}; "
                f"SDK {android_sdks[android_version]}; {performance_version})")
        elif browser_type == 'firefox':
            return (f"Mozilla/5.0 (Android {android_version}; Mobile; rv:{browser_version}.0) "
                    f"Gecko/{browser_version}.0 Firefox/{browser_version}.0")

    elif device_type == 'ios':
        ios_versions = ['13.0', '14.0', '15.0', '16.0', '17.0', '18.0']
        ios_version = random.choice(ios_versions)
        if browser_type == 'chrome':
            return (f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version.replace('.', '_')} like Mac OS X) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) CriOS/{browser_version} Mobile/15E148 Safari/604.1")
        elif browser_type == 'firefox':
            return (f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version.replace('.', '_')} like Mac OS X) "
                    f"AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/{browser_version}.0 Mobile/15E148 Safari/605.1.15")

    elif device_type == 'windows':
        windows_versions = ['10.0', '11.0']
        windows_version = random.choice(windows_versions)
        if browser_type == 'chrome':
            return (f"Mozilla/5.0 (Windows NT {windows_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    f"Chrome/{browser_version} Safari/537.36")
        elif browser_type == 'firefox':
            return (f"Mozilla/5.0 (Windows NT {windows_version}; Win64; x64; rv:{browser_version}.0) "
                    f"Gecko/{browser_version}.0 Firefox/{browser_version}.0")

    elif device_type == 'ubuntu':
        if browser_type == 'chrome':
            return (f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    f"Chrome/{browser_version} Safari/537.36")
        elif browser_type == 'firefox':
            return (f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{browser_version}.0) Gecko/{browser_version}.0 "
                    f"Firefox/{browser_version}.0")

    return None


def is_user_agent_valid(user_agent: str) -> bool:
    return 'Telegram-Android' in user_agent


def get_telegram_custom_params(user_agent: str) -> str | None:
    android_device = re.search(r'Android \d+.*?; (.*?)(?=\))', user_agent)
    if not android_device:
        return None
    android_device = android_device.group(1)
    android_manufacturer = random.choice(manufacturers) if android_device == 'K' else get_manufacturer(android_device)
    if not android_manufacturer:
        return None
    telegram_version = random.choice(telegram_versions)
    performance_version = random.choice(performance_class)
    android_version = re.search(r'Android (\d+(\.\d+)*)', user_agent).group(1).split('.')[0]
    tg_params = f" Telegram-Android/{telegram_version} " \
                f"({android_manufacturer} {android_device}; Android {android_version}; " \
                f"SDK {android_sdks[android_version]}; {performance_version})"
    return tg_params


def get_sec_ch_ua(user_agent: str) -> str:
    browser_version = re.search(r'Chrome/(\d+)', user_agent).group(1)
    return f'"Android WebView";v="{browser_version}", "Chromium";v="{browser_version}", "Not_A Brand";v="24"'


def get_manufacturer(android_device: str) -> str | None:
    for brand in android_devices:
        for model in android_devices[brand]:
            if android_device in model:
                return brand
    return None
