from geopy.geocoders import Nominatim

geoLoc = Nominatim(user_agent="GetLoc")
locname = geoLoc.reverse("-3.853808, -32.423786")
print(locname.address)