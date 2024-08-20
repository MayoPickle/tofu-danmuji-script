import lunardate
from datetime import date

def lunar_to_solar(year, month, day):
    lunar_date = lunardate.LunarDate(year, month, day)
    return lunar_date.toSolarDate()

matching_years = []
target_date = date(1, 4, 11)  # 任意年份的3月31号，年份字段会被忽略

for year in range(2005, 2100):
    solar_date = lunar_to_solar(year, 2, 13)
    if solar_date.month == target_date.month and solar_date.day == target_date.day:
        matching_years.append(year)
    print(f"农历{year}年3月初三对应的阳历日期是：{solar_date}")

print("年份在农历3月初三与阳历3月31号重合的有：", matching_years)
