#!/usr/bin/env python

import datetime
import yaml
from yaml.loader import SafeLoader

# Open the file and load the file
with open('communitycall-data.yml') as f:
    data = yaml.load(f, Loader=SafeLoader)

year = "2023"
day = "Thursday"
i = 0
coords = data['Coordinators']
exceptions = data['Except']
statics = data['Statics']

f = open('communitycall.yml', 'w')
f.write('name: Community call meetings\n')
f.write('timezone: Europe/Berlin\n\n')
f.write('events:\n')

for calendarweek in range(data['CW_start'],data['CW_end']):

    year_week_day = f"{year}/{calendarweek}/{day}"
    result_date = datetime.datetime.strptime(year_week_day, "%Y/%W/%A").strftime("%Y-%m-%d")

    if result_date not in exceptions:

        if result_date in statics:
            coord = coords[statics[result_date]]
        else:
            coord = coords[list(coords)[i]]

        event_string = '''\
 - summary: "Weekly SCS Community Meeting"
   begin: {date} 15:05:00
   duration:
     minutes: 40
   description: |
     Our weekly SCS Community Meeting. This meeting features a round of updates from the various technical teams as well as Special Interest Groups (SIGs). Furthermore the SCS project team gives an update on the overall project.

     Jitsi server on https://conf.scs.koeln:8443/SCS-Tech
     Dial-In: +49-221-292772-611
     Coordinator: {coordinator}
   location: "https://conf.scs.koeln:8443/SCS-Tech"\
'''.format(coordinator=coord, date=result_date)
        f.write(event_string)
        f.write('\n')
        i= i+1

        # reset coord index if end has reached
        if i == len(coords):
            i= 0


f.close()
