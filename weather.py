#!/usr/bin/env python
"""
Weather app using Weather Underground API.

Builds HTML files with weather data and shows them in a lightweight PyQt GUI.

Alternatively (-u option):
Generates a short JSON update string which can be used with CommandRunner
Applet for Cinnamon to show current conditions. Click action is also supplied as
part of the message so that clicking on the Applet opens the weather App.

In either case the fetched data is stored in ~/.weather folder and reused if
a preset time did not elapse since last fetch. That time can be changed using
min argument to Weather constructor. This setup prevents too many queries being
sent to WU API.

Finally, an API key is needed and default key can be set below.
"""

import urllib2
import json
import os
import re
import time

# parse arguments
import argparse

parser = argparse.ArgumentParser(description='Fetch weather and show results.')
parser.add_argument('location', type=str, help='weather location')
parser.add_argument('-m', '--mult', type=float, default=1.0,
                    help='resize GUI by the given factor')
parser.add_argument('-k', '--key', type=str, default="",
                    help='Weather Underground API key')
parser.add_argument('-u', '--update', action='store_true', default=False,
                    help='update files without showing GUI')
parser.add_argument('-s', '--size', type=int, default=12,
                    help='font size for the message string')

args = parser.parse_args()

QUERY = args.location
MULT = args.mult
API_KEY = args.key

# 'icon' field contains a name
# 'icon_url' and/or 'icon' may have nt_ for night: use second option
# fctcode for hourly may have an interesting weather condition number
# names and numbers from
# http://www.wunderground.com/weather/api/d/docs?d=resources/phrase-glossary
# windy, WU do not exist, but we use the icons
ICON = {'chanceflurries': ['41', '46'],
        'chancerain': ['39', '45'],
        'chancesleet': '05',
        'chancesnow': ['41', '46'],
        'chancetstorms': ['37', '47'],
        'clear': ['32', '31'],
        'cloudy': '26',
        'flurries': '14',
        'fog': '20',
        'hazy': ['19', '21'],
        'mostlycloudy': ['28', '27'],
        'mostlysunny': ['34', '33'],
        'partlycloudy': ['30', '29'],
        'partlysunny': ['30', '29'],
        'rain': '12',
        'sleet': '07',
        'snow': '16',
        'sunny': '32',
        'tstorms': '00',
        'windy': '24',
        '7': '36',
        '9': '15',
        '13': '11',
        '11': '12',
        '16': '13',
        '19': '16',
        '21': '14',
        '22': '18',
        '23': '18',
        '24': '15',
        'WU': 'WU',
        }

TREND = {'+': '&nearr;',
         '-': '&searr;',
         '0': ''
         }


class Weather(object):

    """ Wrapper of the Weather Underground API. """

    def __init__(self, query, **options):
        """ Initialize the API query URL. """
        global API_KEY

        self.path = os.path.split(os.path.abspath(__file__))[0]
        self.home = os.path.expanduser('~') + '/.weather'
        try:
            os.mkdir(self.home)
        except:
            pass
        if not API_KEY:
            try:
                with open(self.home+'/API.key', 'r') as f:
                    API_KEY = f.readline().strip()
            except:
                raise RuntimeError("No API key provided or saved.")
        else:
            with open(self.home+'/API.key', 'w') as f:
                print >>f, API_KEY

        features = "alerts/conditions/forecast10day/hourly"
        settings = "bestfct:1"
        fmt = "json"
        self.url = "http://api.wunderground.com/api/{}/{}/{}/q/{}.{}" \
            .format(API_KEY, features, settings, query, fmt)
        print self.url
        self.data = {}
        if 'min' in options:
            self.min = options['min']
        else:
            self.min = 5
        self.old(self.min)
        self.alert = False
        self.file = self.home + '/{}.json' \
            .format(re.sub(r'\W', '_', query))

    def old(self, min=5):
        """ Remove saved weather if older than a number of minutes. """
        try:
            modified = os.path.getmtime(self.file)
            current = time.time()
            if current-modified > min * 60:
                os.unlink(self.file)
        except:
            pass

    def fetch(self):
        """ Get the weather data. """
        self.old(self.min)
        try:
            with open(self.file, 'r') as f:
                self.data = json.load(f)
        except:
            res = urllib2.urlopen(self.url).read()
            self.data = json.loads(res)
            with open(self.file, 'w') as f:
                print >>f, json.dumps(self.data, sort_keys=True, indent=4,
                                      separators=(',', ': '))
        if 'alerts' in self.data and self.data["alerts"]:
            self.alert = True

    def icon(self, name, url, number="0", white=False):
        """ Get appropriate icon from ICON dictionary. """
        night = '/nt_' in url or 'nt_' in name
        name = name.replace('nt_', '')
        if number in ICON:
            icon = ICON[number]
        elif name in ICON:
            icon = ICON[name]
        else:
            icon = 'na'
        # pick day/night version if exist
        if isinstance(icon, list):
            if night:
                icon = icon[1]
            else:
                icon = icon[0]
        if white:
            return "file:{}/png_white/{}.png".format(self.path, icon)
        else:
            return "file:{}/png/{}.png".format(self.path, icon)

    def current(self):
        """ Build HTML code for current conditions. """
        curr = self.data["current_observation"]
        icon = self.icon(curr["icon"], curr["icon_url"])
        time = curr["local_time_rfc822"].replace(curr["local_tz_offset"], '')
        if self.alert:
            time = '<span style="color:red;">' + time + ' * ALERT *</span>'
        html = r"""
        <td style="font-size: 120%;" colspan="8">
        <img src="{}" width="{}" align="left"
        style="padding:0; margin:0;"/>{}<br/><br/>
        <span style="color:green; font-size:200%;">{}&deg;</span>
        (feels like {}&deg;) <br/>
        <span style="font-size:120%;">{}</span><br/>
        <span style="font-size:80%;">Wind: <span
        style="font-size:80%;">{}</span> {}</span><span
        style="font-size:64%;">kph</span><br/>
        <span style="font-size:80%;">{}<span
        style="font-size:64%;">hPa</span>{}</span></td>
        """.format(icon, int(180 * MULT), time, float(curr["temp_c"]),
                   float(curr["feelslike_c"]), curr["weather"],
                   curr["wind_dir"], curr["wind_kph"], curr["pressure_mb"],
                   TREND[curr["pressure_trend"]])
        return html

    def credits(self):
        """ Format Weather Underground logo. """
        icon = self.icon("WU", "")
        logo = self.data["current_observation"]
        return r"""<td colspan="2"> <a href="{}"> <img src="{}" width="{}"/></a>
        </td>
        """.format(logo["forecast_url"], icon, int(100 * MULT))

    def days(self):
        """ Format daily forecast. """
        days = self.data["forecast"]["simpleforecast"]["forecastday"]
        rain = self.icon("rain", "")
        snow = self.icon("snow", "")
        html = r'<tr>'
        totalsnow = 0.0
        for day in days:
            totalsnow += float(day["snow_allday"]["cm"])
        for day in days:
            icon = self.icon(day["icon"], day["icon_url"])
            html += r"""
            <td style="font-size: 100%; padding:10px 0; text-align:center;">
            <div style="width: 100%;">
            <span style="display:block;">{}</span>
            </div>
            <img src="{}" width="{}" style="padding:0 5px;"/><br/>
            <div style="width: 100%;">
            <span style="display:block;">
            <span style="color:red;">{}&deg;</span>
            <span style="color:blue;">{}&deg;</span>
            </span></div>
            <div style="width: 100%;">
            <span style="display:block; color:blue;">
            <img src="{}" width="{}" style="padding:0;"/>{}<span
            style="font-size:80%;">%</span></span>
            </div>
            """.format(day["date"]["weekday_short"], icon, int(50 * MULT),
                       day["high"]["celsius"], day["low"]["celsius"],
                       rain, int(12 * MULT), day["pop"])
            if totalsnow >= 0.1:
                html += r"""
                <div style="width: 100%;">
                <span style="display:block;">
                <img src="{}" width="{}" style="padding:0;"/><span
                style="font-size:80%;">{}</span><span
                style="font-size:64%;">cm</span></span></div>
                """.format(snow, int(10 * MULT), day["snow_allday"]["cm"])
            html += "</td>"
        return html + "</tr>"

    def days_large(self):
        """ Format daily forecast with more data. """
        days = self.data["forecast"]["simpleforecast"]["forecastday"]
        rain = self.icon("rain", "")
        snow = self.icon("snow", "")
        wind = self.icon("windy", "")
        html = r"""<body style="background-color: white;">
        <div style="width:100%;">
        <table style="margin:auto;"><tr>"""
        totalsnow = 0.0
        for day in days:
            totalsnow += float(day["snow_allday"]["cm"])
        for i in range(10):
            if i == 5:
                html += r'</tr><tr>'
            day = days[i]
            icon = self.icon(day["icon"], day["icon_url"])
            html += r"""
            <td style="font-size: 100%; padding:20 10; text-align:center;
            ">
            <div style="width: 100%;">
            <b style="display:block;">{}</b>
            </div>
            <img src="{}" width="{}" style="padding:0;"/><br/>
            <div style="width: 100%;">
            <span style="display:block;">{}</span>
            </div>
            <div style="width: 100%;">
            <span style="display:block; font-size:120%;">
            <span style="color:red;">{}&deg;</span>
            <span style="color:blue;">{}&deg;</span>
            </span></div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}" style="padding:0;"/><span
            style="font-size:120%; color:blue;">{}</span><span
            style="font-size:80%; color:blue;">%</span> {}<span
            style="font-size:80%;">mm</span></span>
            </div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}"
            style="padding:0;"/><span
            style="font-size:70%;">{}</span> {}({})<span
            style="font-size:80%;">kph</span></span>
            </div>
            """.format(day["date"]["weekday_short"], icon, int(80 * MULT),
                       day["conditions"], day["high"]["celsius"],
                       day["low"]["celsius"], rain, int(16 * MULT),
                       day["pop"], day["qpf_allday"]["mm"], wind,
                       int(16 * MULT), day["avewind"]["dir"],
                       day["avewind"]["kph"], day["maxwind"]["kph"])
            if totalsnow >= 0.1:
                html += r"""
                <div style="width: 100%;">
                <span style="display:block;">
                <img src="{}" width="{}"
                style="padding:0;"/> {}<span
            style="font-size:80%;">cm</span></span></div>
                """.format(snow, int(16 * MULT), day["snow_allday"]["cm"])
            html += "</td>"
        return html + "</tr></table></div></body>"

    def txtdays(self):
        """ Format textual forecast. """
        days = self.data["forecast"]["txt_forecast"]["forecastday"]
        html = """<body style="background-color: white;"><table>"""
        for day in days:
            icon = self.icon(day["icon"], day["icon_url"])
            html += r"""
            <tr><td>
        <img src="{}" width="{}" align="left"
        style="padding:0; margin:0;"/></td><td>
            <strong>{}:</strong><br/> {} </td></tr>
        """.format(icon, int(80 * MULT), day["title"], day["fcttext_metric"])
        return html + "</table></body>"

    def hours(self):
        """ Format hourly forecast. """
        hours = self.data["hourly_forecast"]
        rain = self.icon("rain", "")
        snow = self.icon("snow", "")
        cloud = self.icon("cloudy", "")
        html = r"<tr>"
        totalsnow = 0.0
        for hour in hours:
            totalsnow += float(hour["snow"]["metric"])
        for hour in hours[:10]:
            # if i in {8, 16} and not short:
            #    html += r'</tr><tr>'
            icon = self.icon(hour["icon"], hour["icon_url"], hour["fctcode"])
            html += r"""
            <td style="font-size: 100%; padding:10px 0; text-align:center;">
            <div style="width: 100%;">
            <span style="display:block;">{}:00</span>
            </div>
            <img src="{}" width="{}" style="padding:0 5px;"/><br/>
            <div style="width: 100%;">
            <span style="display:block;">
            <span style="color:green;font-size:120%;">{}&deg;</span><span
            style="font-size:90%;">({}&deg;)</span>
            </span></div>
            <div style="width: 100%;">
            <span style="display:block;color:blue;">
            <img src="{}" width="{}" style="padding:0;"/>{}<span
            style="font-size:80%;">%</span></span>
            </div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}" style="padding:0;"/><span
            style="font-size:80%;">{}</span><span
            style="font-size:60%;">%</span></span>
            </div>
            """.format(hour["FCTTIME"]["hour"], icon, int(50 * MULT),
                       hour["temp"]["metric"], hour["feelslike"]["metric"],
                       rain, int(12 * MULT), hour["pop"],
                       cloud, int(10 * MULT), hour["sky"])
            if totalsnow >= 0.1:
                html += r"""
                <div style="width: 100%;">
                <span style="display:block;">
                <img src="{}" width="{}" style="padding:0;"/><span
                style="font-size:80%;">{}</span><span
                style="font-size:64%;">mm</span></span></div>
                """.format(snow, int(10 * MULT), hour["snow"]["metric"])
            html += "</td>"
        return html + "</tr>"

    def hours_large(self):
        """ Format hourly forecast with more details. """
        hours = self.data["hourly_forecast"]
        rain = self.icon("rain", "")
        snow = self.icon("snow", "")
        wind = self.icon("windy", "")
        cloud = self.icon("cloudy", "")
        html = r"""<body style="background-color: white;">
        <div style="width:100%;">
        <table style="margin:auto;"><tr>"""
        totalsnow = 0.0
        for hour in hours:
            totalsnow += float(hour["snow"]["metric"])
        for i in range(24):
            hour = hours[i]
            if i in {5, 10, 15, 20}:
                html += r'</tr><tr>'
            icon = self.icon(hour["icon"], hour["icon_url"], hour["fctcode"])
            html += r"""
            <td style="font-size: 100%; padding:20 10; text-align:center;
            ">
            <div style="width: 100%;">
            <b style="display:block;">{}:00</b>
            </div>
            <img src="{}" width="{}" style="padding:0;"/><br/>
            <div style="width: 100%;">
            <span style="display:block;">{}</span>
            </div>
            <div style="width: 100%;">
            <span style="display:block; font-size:120%;">
            <span style="font-size:120%; color:green;">{}&deg;</span><span
            style="font-size:80%;">({}&deg;)</span>
            </span></div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}" style="padding:0;"/><span
            style="font-size:120%; color:blue;">{}</span><span
            style="font-size:80%; color:blue;">%</span> {}<span
            style="font-size:80%;">mm</span></span>
            </div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}"
            style="padding:0;"/><span
            style="font-size:70%;">{}</span> {}<span
            style="font-size:80%;">kph</span></span>
            </div>
            <div style="width: 100%;">
            <span style="display:block;">
            <img src="{}" width="{}"
            style="padding:0;"/>{}<span
            style="font-size:80%;">%</span>
            """.format(hour["FCTTIME"]["hour"], icon, int(80 * MULT),
                       hour["condition"], hour["temp"]["metric"],
                       hour["feelslike"]["metric"], rain, int(16 * MULT),
                       hour["pop"], hour["qpf"]["metric"], wind, int(16 * MULT),
                       hour["wdir"]["dir"], hour["wspd"]["metric"],
                       cloud, int(16*MULT), hour["sky"], hour["mslp"]["metric"])
            if totalsnow >= 0.1:
                html += r"""
                <img src="{}" width="{}"
                style="padding:0;"/>{}<span
            style="font-size:80%;">mm</span></span>
                """.format(snow, int(16 * MULT), hour["snow"]["metric"])
            html += r"""
            <div style="width: 100%;">
            <span style="display:block;">{}<span
            style="font-size:80%;">hPa</span></span>
            </div>
            </span></div></td>""".format(hour["mslp"]["metric"])
        return html + "</tr></table></div></body>"

    def build_main(self):
        """ Build main HTML file. """
        start = r"""<html><body style="background-color: white;">
        <div style="width:100%;">
        <table style="margin:auto;"><tr>"""
        end = r"</tr></table></div></body></html>"
        html = start + self.current() + self.credits() + "</tr>" + self.hours() \
            + self.days() + end
        return html

    def alerts(self):
        """ Format alerts. """
        if not self.alert:
            return ""
        html = r"""<html><body style="background-color: white;">"""
        for alert in self.data["alerts"]:
            html += r"""<p> <b> {} </b> Expires: {}.</br>
            {}</p>""".format(alert["description"], alert["expires"],
                             re.sub(r'[\s\n]+', ' ',
                                    alert["message"].replace('\n\n', '<br/>')))
        return html + "</body></html>"

    def message(self):
        """ Format JSON weather summary message. """
        curr = self.data["current_observation"]
        hours = self.data["hourly_forecast"]
        icon = self.icon(curr["icon"], curr["icon_url"], white=True)
        action = '{}/weather.py "{}" -m{} -k {}'.format(self.path, QUERY, MULT,
                                                        API_KEY)
        with open(self.home + '/clickaction', 'w') as f:
            print >>f, """#!/bin/bash
(
  flock -xn 200 || exit 1
  {}
) 200>/var/lock/.weather.exclusivelock
""".format(action)
        os.system('chmod +x ' + self.home + '/clickaction')
        small = int(args.size * 0.45)
        message = """
        <xml>
        <appsettings>
            <tooltip>Weather summary for %s.
            Current conditions, then next few hours. </tooltip>
            <clickaction>%s</clickaction>
        </appsettings>
        <item>
            <type>icon</type>
            <value>%s</value>
            <attr>
                <style>icon-size: {4}pt;</style>
            </attr>
        </item>
        <item>
            <type>text</type>
            <value> %s </value>
            <attr>
                <style>font-size: {3}pt; color:white</style>
            </attr>
        </item>
        <item>
            <type>text</type>
            <value>%s</value>
            <attr>
                <style>font-size: {0}pt; color:white</style>
            </attr>
        </item>
        <item>
            <type>text</type>
            <value>O</value>
            <attr>
            <style>font-size: {1}pt; color:white; padding-bottom:{2}pt;</style>
            </attr>
        </item>
        <item>
            <type>text</type>
            <value> | </value>
            <attr>
                <style>font-size: {0}pt; color:white</style>
            </attr>
        </item>
        """ % (QUERY, self.home + '/clickaction', icon, curr["weather"],
               int(curr["temp_c"]))
        message = message.format(args.size, small,
                                 args.size - small - args.size % 4,
                                 int(args.size * 0.8), int(args.size * 1.1))
        args.size = int(args.size * 0.85)
        small = int(args.size * 0.45)
        for hour in hours[0:5:2]:
            icon = self.icon(hour["icon"], hour["icon_url"], hour["fctcode"],
                             white=True)
            message += """
            <item>
            <type>icon</type>
            <value>%s</value>
            <attr>
                <style>icon-size: {4}pt;</style>
            </attr>
            </item>
            <item>
                <type>text</type>
                <value>%s</value>
                <attr>
                    <style>font-size: {0}pt; color:white</style>
                </attr>
            </item>
            <item>
                <type>text</type>
                <value>O</value>
                <attr>
                <style>font-size: {1}pt; color:white; padding-bottom:{2}pt;
                </style>
                </attr>
            </item>
            <item>
                <type>text</type>
                <value>%s%% </value>
                <attr>
                    <style>font-size: {3}pt; color:white</style>
                </attr>
            </item>
            """ % (icon, hour["temp"]["metric"], hour["pop"])
        message += '</xml>'
        print message.format(args.size, small,
                             args.size - small - args.size % 4,
                             int(args.size * 0.8), int(args.size * 1.1))


if __name__ == "__main__":
    # build tabs
    weather = Weather(QUERY, min=2)
    weather.fetch()

    # JSON message and exit
    if args.update:
        weather.message()
        exit(0)

    # build interface
    tabs = [(weather.build_main(), "Summary", MULT),
            (weather.hours_large(), "Next 24 hours", MULT),
            (weather.days_large(), "Forecast 10 days", MULT),
            (weather.txtdays(), "Text forecast", MULT)]
    if weather.alert:
        tabs.append((weather.alerts(), "*** ALERT ***", MULT))

    from quicktabs import QuickTabs
    app, win = QuickTabs.App(100 + 640 * MULT, 100 + 480 * MULT)
    win.addTabs(tabs)
    app.exec_()
