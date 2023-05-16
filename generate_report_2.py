import pandas as pd

# a function \that calculates the dew point based on temperature and humidity values.
def calculate_dew_point(temperature, humidity):
    dew_point = temperature - ((100.0 - humidity) / 5.0)
    return dew_point


def process_access_periods(df):
    # find the staff member code from the 'User' column
    staff_members = df['User'].unique()

    for staff_member in staff_members:
        # filter the data for the current staff member
        staff_data = df[df['User'] == staff_member]

        ## Initialize variables for tracking access periods
        access_periods = []
        total_time = 0
        lowest_dew_point = float('inf')

        start_time = None
        end_time = None
        highest_temperature = float('-inf')
        access_readings = []

        # iterating over each row in the staff member's data
        for _, row in staff_data.iterrows():
            timestamp = pd.to_datetime(row['Timestamp'])
            temperature = row['Temperature (C)']
            humidity = row['Humidity (%)']

            if pd.isnull(temperature) or pd.isnull(humidity):
                continue
            # Check if it's the first row for an access period
            if start_time is None:
                start_time = timestamp
                end_time = timestamp
                highest_temperature = temperature
            else:
                # Check if the time gap between the current row and the previous row is more than 1 second

                if (timestamp - end_time).total_seconds() > 1:
                    access_periods.append({
                        'Staff Member': staff_member,
                        'Start Time': start_time,
                        'End Time': end_time,
                        'Duration (seconds)': (end_time - start_time).total_seconds(),
                        'Highest Temperature': highest_temperature,
                        'Lowest Dew Point': lowest_dew_point,
                        'Readings': access_readings
                    })

                    # Update total time and reset variables for the next access period

                    total_time += (end_time - start_time).total_seconds()
                    lowest_dew_point = float('inf')

                    start_time = timestamp
                    highest_temperature = temperature
                    access_readings = []

            end_time = timestamp
            highest_temperature = max(highest_temperature, temperature)
            dew_point = calculate_dew_point(temperature, humidity)
            lowest_dew_point = min(lowest_dew_point, dew_point)
            access_readings.append({
                'Timestamp': timestamp,
                'Temperature': temperature,
                'Humidity': humidity,
                'Dew Point': dew_point
            })

        # Add the last access period if it's ongoing at the end of the data

        if start_time is not None:
            access_periods.append({
                'Staff Member': staff_member,
                'Start Time': start_time,
                'End Time': end_time,
                'Duration (seconds)': (end_time - start_time).total_seconds(),
                'Highest Temperature': highest_temperature,
                'Lowest Dew Point': lowest_dew_point,
                'Readings': access_readings
            })

            total_time += (end_time - start_time).total_seconds()

        # Print the results for the staff member
        print(f"Staff Member: {staff_member}")
        for access_period in access_periods:
            print(f"Access Period:")
            print(f"  Start Time: {access_period['Start Time']}")
            print(f"  End Time: {access_period['End Time']}")
            print(f"  Duration (seconds): {access_period['Duration (seconds)']}")
            print(f"  Highest Temperature: {access_period['Highest Temperature']}")
            print(f"  Lowest Dew Point: {access_period['Lowest Dew Point']}")
            print(f"  Readings:")
            for reading in access_period['Readings']:
                print(
                    f"    Timestamp: {reading['Timestamp']}, Temperature: {reading['Temperature']}, Humidity: {reading['Humidity']}, Dew Point: {reading['Dew Point']}")

        print(f"Total Time: {total_time}")
        print(f"Lowest Dew Point Recorded: {lowest_dew_point}\n")

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('bme680_data.csv')

# Drop any rows with missing values
df = df.dropna()

# Convert the 'Timestamp' column to datetime format
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Sort the DataFrame by timestamp
df = df.sort_values(by='Timestamp')

# Process the access periods
process_access_periods(df)
