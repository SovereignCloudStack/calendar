#!/usr/bin/env python3
"""
Fix RRULE UNTIL values in ICS files to be RFC 5545 compliant.

According to RFC 5545 Section 3.3.10:
"If the DTSTART property is specified as a date with UTC time or a date 
with local time and time zone reference, then the UNTIL rule part MUST 
be specified as a date with UTC time."

This script ensures that RRULE UNTIL values include the 'Z' suffix when
DTSTART uses a TZID parameter.

Usage:
    python fix_ics_rrule.py input.ics [output.ics]
    
If output.ics is not specified, it will overwrite the input file.
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def extract_timezone_from_dtstart(dtstart_line):
    """
    Extract timezone information from a DTSTART line.
    
    Handles various formats including:
    - DTSTART;TZID=Europe/Berlin:20250221T090500
    - DTSTART;TZID=/ics.py/2020.1/Europe/Berlin:20250221T090500
    
    Returns:
        tuple: (timezone_name, is_utc) where is_utc indicates if DTSTART is already in UTC
    """
    # Check if DTSTART is in UTC format (ends with Z)
    if dtstart_line.endswith('Z'):
        return None, True
    
    # Check if DTSTART has no timezone (floating time)
    if 'TZID=' not in dtstart_line:
        return None, False
    
    # Extract TZID value
    tzid_match = re.search(r'TZID=([^:;]+)', dtstart_line)
    if not tzid_match:
        return None, False
    
    tzid = tzid_match.group(1)
    
    # Handle /ics.py/version/Timezone/Name format
    # Extract the actual timezone (last two path components for standard timezones)
    if '/' in tzid:
        parts = tzid.split('/')
        # Filter out empty parts and 'ics.py' and version numbers
        clean_parts = [p for p in parts if p and p != 'ics.py' and not re.match(r'^\d{4}\.\d+$', p)]
        
        # Reconstruct timezone name (usually last 1-2 components)
        if len(clean_parts) >= 2:
            # Most timezones are Continent/City format
            tzid = '/'.join(clean_parts[-2:])
        elif len(clean_parts) == 1:
            tzid = clean_parts[0]
    
    return tzid, False


def convert_local_to_utc(datetime_str, timezone_name):
    """
    Convert a local datetime string to UTC.
    
    Args:
        datetime_str: String in format YYYYMMDDTHHMMSS
        timezone_name: IANA timezone name (e.g., 'Europe/Berlin')
    
    Returns:
        String in format YYYYMMDDTHHMMSSZ (UTC)
    """
    try:
        import pytz
        
        # Parse the datetime string
        dt = datetime.strptime(datetime_str, '%Y%m%dT%H%M%S')
        
        # Get timezone
        tz = pytz.timezone(timezone_name)
        
        # Localize to the timezone (handles DST properly)
        dt_local = tz.localize(dt)
        
        # Convert to UTC
        dt_utc = dt_local.astimezone(pytz.UTC)
        
        # Format back to string with Z suffix
        return dt_utc.strftime('%Y%m%dT%H%M%SZ')
    
    except Exception as e:
        print(f"Warning: Could not convert {datetime_str} in timezone {timezone_name} to UTC: {e}", 
              file=sys.stderr)
        print(f"         Appending 'Z' without conversion (may be incorrect!)", file=sys.stderr)
        # Fallback: just append Z (not ideal but maintains format)
        return datetime_str + 'Z'


def fix_until_in_rrule(rrule_line, timezone_name, dtstart_is_utc):
    """
    Fix UNTIL values in an RRULE line to be RFC 5545 compliant.
    
    Args:
        rrule_line: The RRULE line to fix
        timezone_name: The timezone of the associated DTSTART
        dtstart_is_utc: Whether DTSTART is already in UTC
    
    Returns:
        Fixed RRULE line
    """
    # If DTSTART is not timezone-aware (floating time), no fix needed
    if timezone_name is None and not dtstart_is_utc:
        return rrule_line
    
    # Check if RRULE has an UNTIL value
    if 'UNTIL=' not in rrule_line:
        return rrule_line
    
    # Check if UNTIL already has a Z suffix (already in UTC)
    if re.search(r'UNTIL=\d{8}T\d{6}Z', rrule_line):
        return rrule_line
    
    # Check if UNTIL is a date-only value (no time component)
    # Date-only values don't need the Z suffix according to RFC 5545
    if re.search(r'UNTIL=\d{8}(?:[;\s]|$)', rrule_line):
        return rrule_line
    
    # Find UNTIL datetime value without Z
    until_match = re.search(r'UNTIL=(\d{8}T\d{6})(?=[;\s]|$)', rrule_line)
    if not until_match:
        return rrule_line
    
    until_value = until_match.group(1)
    
    # Convert to UTC if we have timezone information
    if timezone_name:
        until_utc = convert_local_to_utc(until_value, timezone_name)
    else:
        # DTSTART is in UTC, so assume UNTIL is too
        until_utc = until_value + 'Z'
    
    # Replace the UNTIL value
    fixed_line = rrule_line.replace(f'UNTIL={until_value}', f'UNTIL={until_utc}')
    
    return fixed_line


def fix_ics_file(input_path, output_path=None):
    """
    Fix RRULE UNTIL values in an ICS file.
    
    Args:
        input_path: Path to input ICS file
        output_path: Path to output ICS file (optional, defaults to input_path)
    
    Returns:
        Number of RRULE lines that were fixed
    """
    if output_path is None:
        output_path = input_path
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    result = []
    fixes_count = 0
    
    # Track state as we parse the file
    current_timezone = None
    current_dtstart_is_utc = False
    in_vevent = False
    
    for line in lines:
        # Track when we're in a VEVENT
        if line.strip() == 'BEGIN:VEVENT':
            in_vevent = True
            current_timezone = None
            current_dtstart_is_utc = False
        elif line.strip() == 'END:VEVENT':
            in_vevent = False
            current_timezone = None
            current_dtstart_is_utc = False
        
        # Extract timezone from DTSTART
        if in_vevent and line.startswith('DTSTART'):
            current_timezone, current_dtstart_is_utc = extract_timezone_from_dtstart(line)
            result.append(line)
        
        # Fix RRULE if needed
        elif in_vevent and line.startswith('RRULE:'):
            original_line = line
            fixed_line = fix_until_in_rrule(line, current_timezone, current_dtstart_is_utc)
            
            if fixed_line != original_line:
                fixes_count += 1
                print(f"Fixed RRULE:", file=sys.stderr)
                print(f"  Before: {original_line}", file=sys.stderr)
                print(f"  After:  {fixed_line}", file=sys.stderr)
            
            result.append(fixed_line)
        
        else:
            result.append(line)
    
    # Write output
    fixed_content = '\n'.join(result)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return fixes_count


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python fix_ics_rrule.py input.ics [output.ics]", file=sys.stderr)
        print("\nIf output.ics is not specified, the input file will be modified in place.", 
              file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Check if pytz is available
        try:
            import pytz
        except ImportError:
            print("Warning: pytz module not found. Timezone conversions may be incorrect.", 
                  file=sys.stderr)
            print("Install with: pip install pytz", file=sys.stderr)
            print("", file=sys.stderr)
        
        fixes_count = fix_ics_file(input_file, output_file)
        
        if output_file:
            print(f"\nFixed {fixes_count} RRULE(s) in {input_file}", file=sys.stderr)
            print(f"Output written to: {output_file}", file=sys.stderr)
        else:
            print(f"\nFixed {fixes_count} RRULE(s) in {input_file}", file=sys.stderr)
            print(f"File modified in place.", file=sys.stderr)
        
        if fixes_count == 0:
            print("No RRULE fixes were needed - file is already compliant!", file=sys.stderr)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
