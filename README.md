
![GitHub Release](https://img.shields.io/github/v/release/iprak/weatherapi)
[![License](https://img.shields.io/packagist/l/phplicengine/bitly)](https://packagist.org/packages/phplicengine/bitly)
<a href="https://buymeacoffee.com/leolite1q" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" height="20px"></a>

## Summary

The `WeatherAPI` integration displays weather forecast, air quality and ultra violet data from [WeatherAPI](https://www.weatherapi.com/).

You should see 3 entities generated for a location starting with the id:

- sensor.weatherapi\_
- air*quality.weatherapi*
- weather.weatherapi\_

## Installation

- First obtain a free API key by signing up with [WeatherAPI](https://www.weatherapi.com/). The free API key is limited to 3 day forecast and 1,000,000 calls per month. You can get 5 or more days of forecast with a [paid account](https://www.weatherapi.com/pricing.aspx).
- Download all the files from `custom_components/weatherapi/` into `<config directory>/custom_components/weatherapi/`.
- Restart HomeAssistant.
- `WeatherAPI` can now be added to your Home Assistant instance via the user interface, by using the `Add Integration` button in Integrations page on your Home Assistant instance.
- You should see one weather entity and some air quality/UV index entities. All entity ids will start as `weather/sensor.weatherapi_location`. Entity id can be adjusted from `Entities` page.

## Configuration

The integration can be configured using the `CONFIGURE` button on the Integrations page.

![image](https://user-images.githubusercontent.com/6459774/212574703-8942d9f5-bbfe-4870-a5d5-96d72fefdd7c.png)

- Configure generation of weather related sensors. If unchecked, the sensors would become disabled and would need to be manually deleted.
- Configure generation of forecast and hourly forecast.
- Configure hourly forecast to start at midnight or the current hour.

## Additional Data

- The weather entity has the `reported_condition` which is the original reported condition ([condition codes](https://www.weatherapi.com/docs/weather_conditions.json)).

## Breaking Changes

- [v0.7](https://github.com/iprak/weatherapi/releases): If you had upgraded to v0.6 then the previous UV and air_quality entities will appear unavailable. Now individual entities for air quality parameters are created.
- [v0.6](https://github.com/iprak/weatherapi/releases): You might get duplicated/invalid entity after upgrading to v0.6. This can be fixed by deleting the inactive entity and adjusting the id of the active entity from `Configuration -> Devices & Services -> Entities`.
