from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import seaborn as sns
import numpy as np
from datetime import *
from time import *
import folium
from gpsutils import *


# Loading the file & building the tree scructure
content = open('files_GPX/Sparnatrail.gpx')
soup = BeautifulSoup(content, 'lxml')

### FUNCTIONS
def duration(t1, t2):
  start = datetime.strptime(t1[0:19],'%Y-%m-%dT%H:%M:%S')
  end   = datetime.strptime(t2[0:19],'%Y-%m-%dT%H:%M:%S') 
  duration = end-start 

  return duration.total_seconds()


# GPW file browsing & data extraction
times = []
latitude = []
longitude = []
altitude = []

# Path og the tree structure
for meta in soup.find_all('metadata'):
    for timer in soup.find_all('time'):
        times.append(timer.string)   
    for point in soup.find_all('trkpt'):
        latitude.append(float(point['lat']))
        longitude.append(float(point['lon']))
        for alt in point.children:
            if alt.name == 'ele':
                altitude.append(float(alt.string))


# Calculation time
Date = times[0][0:10]
RunningTime = strftime('%H:%M:%S', gmtime(duration(times[0],times[len(times)-1])))

# Negative & Positive elevation gain
MaxAltitude = np.max(altitude)
MinAltitude = np.min(altitude)
MaxAltitudeIndex = 0
MinAltitudeIndex = 0

DnP = 0
DnN = 0
for i in range(len(altitude)-1):
    #
    if altitude[i] == MaxAltitude:
        MaxAltitudeIndex = i
    #
    if altitude[i] == MinAltitude:
        MinAltitudeIndex = i
    #
    if altitude[i+1] > altitude[i]:
        DnP = DnP + float(altitude[i+1]) - float(altitude[i])
    else:
        DnN = DnN + float(altitude[i]) - float(altitude[i+1])


# Find the indexes h+1,h+2
perHour = [0]
hour = int(times[0][11:13]) + 1
if hour < int(times[len(times)-1][11:13]):
    for u in range(len(times)):
        if len(str(int(times[u][11:13]))) == 1: 
            for sec in np.arange(3,8):
                if f"{times[u]}" == f"2022-11-13T0{hour}:45:3{sec}.000Z":
                    perHour.append(u)
                    hour += 1
        else:
            for sec in np.arange(3,8):
                if f"{times[u]}" == f"2022-11-13T{hour}:45:3{sec}.000Z":
                    perHour.append(u)
                    hour += 1
perHour.append(len(times)-2)


# Distance travelled per hour (m/1000 -> km)
distance = [0]
distance_cumul = [0]
for d in range(len(perHour)-1):
    distPerHour = []
    for p in np.arange(perHour[d],perHour[d+1]):
        distPerHour.append(great_circle_distance(latitude[p+1],longitude[p+1], latitude[p],longitude[p]))
    distance.append(round(np.sum(distPerHour)/1000,2))
    distance_cumul.append(round(distance_cumul[len(distance_cumul)-1]+round(np.sum(distPerHour)/1000,2),2))

# Get all distances and duration between each geographic coordinate
all_distance = []
all_duration = []
for k in range(len(times)-2):
    all_distance.append(great_circle_distance(latitude[k+1],longitude[k+1],latitude[k],longitude[k]))
    all_duration.append(duration(times[k],times[k+1]))

# Vitesse in meters/sec*3.6 -> km/h
vitesse = []
for i in range(len(all_distance)-1):
    vitesse.append((all_distance[i+1]/all_duration[i+1])*3.6)



#### CARTOGRAPHY
# Geographical position (latitude, longitude)
points = []
for k in range(len(latitude)):
    points.append((latitude[k],longitude[k]))

# Creating a map centred around a coordinate
fmap = folium.Map(location=[latitude[0], longitude[0]], tiles='OpenStreetMap', zoom_start=12)
# Display of the race route on the map
for g in range(len(latitude)-3):
    if vitesse[g] < 5.0:
        folium.PolyLine([(latitude[g],longitude[g]),(latitude[g+1],longitude[g+1])], color='green', weight=2.5, opacity=0.8).add_to(fmap)
    elif vitesse[g] < 10.0 and vitesse[g] > 5.0:
        folium.PolyLine([(latitude[g],longitude[g]),(latitude[g+1],longitude[g+1])], color='orange', weight=2.5, opacity=0.8).add_to(fmap)
    elif vitesse[g] < 15.0 and vitesse[g] > 10.0:
        folium.PolyLine([(latitude[g],longitude[g]),(latitude[g+1],longitude[g+1])], color='red', weight=2.5, opacity=0.8).add_to(fmap)
    elif vitesse[g] < 20.0 and vitesse[g] > 15.0:
        folium.PolyLine([(latitude[g],longitude[g]),(latitude[g+1],longitude[g+1])], color='darkred', weight=2.5, opacity=0.8).add_to(fmap)



# Adding markers on the map
## START
folium.Marker([latitude[0],longitude[0]],
              popup=f"Start: {times[0][11:19]} ({distance_cumul[0]}km)",
              icon=folium.Icon(color='green',icon='glyphicon glyphicon-play')).add_to(fmap)
## END
folium.Marker([latitude[-1],longitude[-1]],
              popup=f"End: {times[len(times)-1][11:19]} ({distance_cumul[len(distance_cumul)-1]}km)",
              icon=folium.Icon(color='red',icon='glyphicon glyphicon-stop')).add_to(fmap)

## Altitude peak
folium.Marker([latitude[MaxAltitudeIndex],longitude[MaxAltitudeIndex]],
              popup=f"Altitude peak: {round(MaxAltitude,2)}m",
              icon=folium.Icon(color='lightred',icon='glyphicon glyphicon-chevron-up')).add_to(fmap)

## Altitude trough
folium.Marker([latitude[MinAltitudeIndex],longitude[MinAltitudeIndex]],
              popup=f"Altitude trough: {round(MinAltitude,2)}m",
              icon=folium.Icon(color='lightblue',icon='glyphicon glyphicon-chevron-down')).add_to(fmap)

# Position at each hour
for t in range(len(perHour[1:-1])):
    folium.Marker([latitude[perHour[t+1]],longitude[perHour[t+1]]],
              popup=f"{times[perHour[t+1]][11:19]} ({distance_cumul[t+1]}km)",
              icon=folium.Icon(color='pink',icon='glyphicon glyphicon-time')).add_to(fmap)

# Generation of the HTML file containg the map
fmap.save('html/SparnaTrail.html')




# PLOTTING
fig, ax = plt.subplots()

### IMAGE
arr_lena = mpimg.imread('img/Sparnatrail.jpg')
imagebox = OffsetImage(arr_lena, zoom=0.13)
ab = AnnotationBbox(imagebox, (4900, 50))
ax.add_artist(ab)

### DATA
x = range(len(altitude))
y = altitude
plt.plot(x, y)

# Colors according to the elevation
for x1, x2, y1, y2 in zip(x,x[1:],y,y[1:]):
    if y1 > y2:
        plt.plot([x1, x2], [y1, y2], 'r')
    elif y1 < y2:
        plt.plot([x1, x2], [y1, y2], 'g')
    else:
        plt.plot([x1, x2], [y1, y2], 'b')

# TEXT
plt.text(x=len(altitude)-1000,y=300,s=f"{round(DnP,1)}D+",c='r',fontweight='bold',backgroundcolor='k')      
plt.text(x=len(altitude)-2300,y=300,s=f"{round(DnN,1)}D-",c='g',fontweight='bold',backgroundcolor='k')      
        
# Parameters
plt.ylabel('Altitude (m)',fontweight='bold')
plt.ylim(0,320)
plt.title(str(Date),c='r',fontweight='bold')
plt.suptitle('SparnaTrail', fontweight='bold',fontsize=20)
plt.tick_params(labelbottom=False)
plt.annotate(str(round(MaxAltitude,2))+'m',xy=(MaxAltitudeIndex,MaxAltitude+0.001),xytext=(MaxAltitudeIndex-300,MaxAltitude+30),arrowprops=dict(facecolor='magenta',shrink=0.05),fontweight='bold',c='m')
plt.annotate(str(round(MinAltitude,2))+'m',xy=(MinAltitudeIndex,MinAltitude+0.001),xytext=(MinAltitudeIndex-300,MinAltitude-40),arrowprops=dict(facecolor='cyan',shrink=0.05),fontweight='bold',c='c')
plt.grid(axis='y')
###
plt.show()


