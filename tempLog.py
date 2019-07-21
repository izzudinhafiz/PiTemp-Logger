import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta, date
pd.options.mode.chained_assignment = None

url = "http://192.168.1.103/data_log.csv"

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

# data = pd.read_csv("data_log.csv")
data = pd.read_csv(url)

data["Date"] = data["Date"] + " " + data["Time"]
del data["Time"]
data["Date"] = pd.to_datetime(data["Date"], infer_datetime_format=True)
data["Date"] = data["Date"].apply(lambda x: x.replace(microsecond=0))
data.set_index("Date", inplace=True)

data["Temperature"] = data["Temperature"].rolling(window=35, center=True).mean()
data["Delta"] = np.gradient(data["Temperature"].values)
data["Delta"] = data["Delta"].rolling(window=5, center=True).mean()
data.dropna(inplace=True)

onThreshold = -0.043
offThreshold = 0.024

data["On"] = data["Delta"] < onThreshold
data["Off"] = data["Delta"] > offThreshold
data["On"].loc[data["On"] == True] = 1
data["On"].loc[data["On"] == False] = 0
data["Off"].loc[data["Off"] == True] = 1
data["Off"].loc[data["Off"] == False] = 0

currentlyOn = 0
currentlyOff = 0
firstCase = 1

for i in range(len(data)):
    if data["On"].iloc[i] == 1 and currentlyOn == 0 and firstCase == 1:
        currentlyOn = 1
        firstCase = 0
        eof = 0
        n = i
        while eof == 0:
            n += 1
            if data["Off"].iloc[n] == 1:
                eof = 1
                data["On"].iloc[i:n] = 1

    elif data["Off"].iloc[i] == 1 and currentlyOff == 0 and firstCase == 1:
        currentlyOff = 1
        firstCase = 0
        eof = 0
        n = i
        while eof == 0:
            n += 1
            if data["On"].iloc[n] == 1:
                eof = 1
                data["Off"].iloc[i:n] = 1

    elif data["On"].iloc[i] == 1 and currentlyOn == 0 and firstCase == 0:
        currentlyOn = 1
        currentlyOff = 0
        eof = 0
        n = i
        while eof == 0:
            if n == len(data):
                data["On"].iloc[i:n] = 1
                eof = 1
            elif data["Off"].iloc[n] == 1:
                eof = 1
                data["On"].iloc[i:n] = 1
            n += 1

    elif data["Off"].iloc[i] == 1 and currentlyOff == 0 and firstCase == 0:
        currentlyOff = 1
        currentlyOn = 0
        eof = 0
        n = i
        while eof == 0:
            if n == len(data):
                data["Off"].iloc[i:n] = 1
                eof = 1
            elif data["On"].iloc[n] == 1:
                eof = 1
                data["Off"].iloc[i:n] = 1
            n += 1



startDate = date(2018, 7, 17)
endDate = date.today() + timedelta(days=1)
d = {}
for single_date in daterange(startDate, endDate):
    d[single_date.strftime("%Y-%m-%d")] = round((data["On"].loc[single_date.strftime("%Y-%m-%d")].sum() / 1440.0) * 24.0, 2)

d = pd.Series(d)
d = pd.DataFrame(d)
d.columns = ["Usage"]
d.index.names = ["Date"]

# Start Date of Data 2018-07-17
averageOnTime = round((d["Usage"].mean()), 2)
print("Daily Usage Average:",averageOnTime, "Hours | Cost/Month: RM", round(averageOnTime * 0.47 * 0.9 * 30,2))

onTimeMonthly = round(d["Usage"][-30:].sum(), 2)
print("Last 30 days usage:", onTimeMonthly, "hours | Cost this month: RM", round(onTimeMonthly * 0.47 * 0.9,2) )

usageToday = round(data["On"][date.today().strftime("%Y-%m-%d"):].sum()/60, 2)
print("Today's usage:",usageToday, "Hours | One week average:", round(d["Usage"][-7:].mean(),2), "hours")
print("Current temp:", round(data["Temperature"][-1:].values[0],2), "Celcius")
print(" ")
print(d[-7:])

data["On"].loc[data["On"] == True] = 35
data["On"].loc[data["On"] == False] = 25
data["Off"].loc[data["Off"] == True] = 35
data["Off"].loc[data["Off"] == False] = 25


start_date = str(date.today() - timedelta(days=1))
end_date = str(date.today() + timedelta(days=1))

start_date = "2018-09-16"
end_date = "2018-09-23"

plt.subplot(211)
data["Temperature"].loc[start_date : end_date].plot(grid=True)
plt.fill_between(data.loc[start_date : end_date].index, 25, data["On"].loc[start_date : end_date], color="g", alpha=0.5)
plt.ylim(25)

plt.subplot(212)
data["Temperature"] = (data["Temperature"] - data["Temperature"].min())/(data["Temperature"].max() - data["Temperature"].min()) /10
data["Delta"].loc[start_date : end_date].plot(color="k", alpha=0.5)
plt.axhline(onThreshold, color="g")
plt.axhline(offThreshold, color="r")

plt.show()
