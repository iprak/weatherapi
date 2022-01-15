# Summary

The `WeatherAPI` integration displays weather forecast, air quality and ultra violet data from [WeatherAPI](https://www.weatherapi.com/).

You should see 3 entities generated for a location starting with the id:
* sensor.weatherapi_
* air_quality.weatherapi_
* weather.weatherapi_


# Installation

* First obtain a free API key by signing up with [WeatherAPI](https://www.weatherapi.com/). The free API key is limited to 3 day forecast and 1,000,000 calls per month. You can get 5 or more days of forecast with a [paid account](https://www.weatherapi.com/pricing.aspx).
* Download all the files from `custom_components/weatherapi/` into `<config directory>/custom_components/weatherapi/`.
* Restart HomeAssistant.
* `WeatherAPI` can now be added to your Home Assistant instance via the user interface, by using the `Add Integration` button in Integrations page on your Home Assistant instance.
* You should see one weather entity and some air quality/UV index entities. All entity ids will start as `weather/sensor.weatherapi_location`. Entity id can be adjusted from `Entities` page.

# Configuration
The integration can be configured to generate hourly forecast using the `CONFIGURE` button on the Integrations page.



# Breaking Changes
* [v0.7](https://github.com/iprak/weatherapi/releases): If you had upgraded to v0.6 then the previous UV and air_quality entities will appear unavailable. Now individual entities for air quality parameters are created.
* [v0.6](https://github.com/iprak/weatherapi/releases): You might get duplicated/invalid entity after upgrading to v0.6. This can be fixed by deleting the inactive entity and adjusting the id of the active entity from `Configuration -> Devices & Services -> Entities`.