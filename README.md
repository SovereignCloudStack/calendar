# Public SCS community calendar
This repository contains various `yaml` files to announce public events, meetings and other interesting happenings of 
our [Sovereign Cloud Stack](https://scs.community) community.

# Import public SCS communuty calendar
The public calendar is automatically published at <https://sovereigncloudstack.github.io/calendar/scs.ics>. We recommend importing the calendar with an iCalendar client like [Thunderbird](https://support.mozilla.org/en-US/kb/creating-new-calendars#w_on-the-network-connect-to-your-online-calendars).

## Converting to `ics`
We'll make use of the python script [yaml2ics](https://github.com/scientific-python/yaml2ics), which in turn will automatically be published in a seperate branch.

## Testing locally
If you want to test the generation of our public calendar locally, simpkly install [yaml2ics](https://github.com/scientific-python/yaml2ics):
```
python -m pip install --upgrade pip
pip install yaml2ics
pip install -r requirements.txt
```
and call `yaml2ics` on `main.yml` (or any of the sub-calendars):
```
yaml2ics main.yml > ./scs.ics
```
