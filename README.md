To test this iot system, both mqtt publisher and mqtt subscriber need to be running at the same time. With mqtt publisher we define door access and with mqtt subscriber we take measurements and log then when someone has entered the door and the access period has started. Below I analzye further how each one exactly works. 

MQTT Publisher 

First, I modified the given mqtt\_pub\_simulated.py to create the Door Access Control System I was asked to. This report provides an in-depth overview of the system's components, functionality, and operation. 

The Door Access Control System is a simulated implementation of an access control system using an ESP32-based board (Huzzah32) and various sensors and peripherals. The system allows users to enter or exit a controlled area by entering a valid user code. The system utilizes MQTT (Message Queuing Telemetry Transport) protocol to publish door access events (entering, exiting, user codes) to a public MQTT broker.  

**The Door Access Control System consists of the following main components:** 

1. Huzzah32 Board: The main controller of the system, providing processing power, I/O interfaces, and connectivity options. 
1. BME680 Environmental Sensor: Measures temperature, humidity, pressure, and gas levels in the controlled area. 
1. NeoPixel LED Strip: Indicates the status of the controlled area with 32 RGB LEDs. 
1. OLED FeatherWing Display: Provides visual feedback and user interaction, displaying system status, messages, and time. 
1. WiFi and MQTT Connectivity: Connects the system to a local network and a public MQTT broker for publishing events and receiving messages. 

**System Functionality:** 

1. Initialization: Sets up hardware components, establishes connections, and registers to the MQTT broker. 
1. User Code Validation: Validates user codes against a list of valid codes for access control. 
1. Access Control: Grants access if the area is unoccupied and the user code is valid. Publishes entry events and updates LED strip and OLED display. 
4. Occupancy Status: Tracks occupancy and denies access until the current occupant exits. Publishes exit events and updates LED strip and OLED display. 
4. Real-Time Clock (RTC) and Time Synchronization: Utilizes the RTC feature to maintain accurate time information synchronized with an NTP server. 
4. Button Inputs: Uses buttons on the OLED display for additional functionality (not assigned in the provided code). 

**Program Execution:** 

The program execution follows the structure of the MainApp class, which inherits from the IoTApp class. The class provides an execution loop that consists of three main methods: init(), loop(), and deinit(). 

1) Initialization method 

The init() method is responsible for initializing the system components and establishing connections. It initializes the BME680 sensor, sets up the NeoPixel LED strip, connects to the WiFi network, and registers to the MQTT broker. It also sets up the OLED display and initializes door access control variables. 

2) Main Loop method 

The loop() method is the heart of the program and runs continuously in a loop. It prompts the user to enter their desired action (entering or exiting) and user code. It validates the user code, grants or denies access based on the current occupancy status, and publishes MQTT messages accordingly. It updates the NeoPixel LED strip and OLED display to reflect the current access status and user information. The loop also includes a short delay between iterations. 

3) Deinit method 

The deinit() method is called after the main loop finishes execution. It performs any necessary cleanup operations, such as shutting down sensor devices or releasing resources. In the provided code, the deinit() method is empty, as no specific cleanup operations are implemented. 

**User Interaction and Output:** 

The OLED FeatherWing display provides visual feedback and user interaction. It shows the current time, system status, messages, and access notifications. Button inputs on the OLED display allow for additional functionality, although not assigned in the provided code. 

**Conclusion** 

The Door Access Control System is a simulated implementation of an access control system using an ESP32-based board and various sensors and peripherals. It provides functionality for validating user codes, granting or denying access, and publishing door access events to an MQTT broker. The system utilizes environmental monitoring, LED indicators, and an OLED display for real-time feedback and interaction. While the provided code is a simulation and may require modifications to work with actual hardware, it serves as a foundation for developing a functional door access control system. 


MQTT Subscriber 

Now let’s move on to the MQTT Subscriber System. I wll provide an overview and detailed explanation of an MQTT subscriber system implemented using the Huzzah32 board, an ESP32-based microcontroller. The system utilizes various components, including the BME680 sensor for temperature, pressure, humidity, and gas resistance measurements, an OLED display for visual output, and NeoPixel LEDs for visual indicators. The system leverages the MQTT (Message Queuing Telemetry Transport) protocol for communication with an MQTT broker, allowing it to receive messages and respond accordingly. 

**System Architecture:** 

The MQTT subscriber system consists of the following main components: 

Huzzah32 Board: The central processing unit that runs the Python script responsible for MQTT communication, sensor readings, and data processing. 

BME680 Sensor: An environmental sensor providing temperature, pressure, humidity, and gas resistance measurements. It connects to the Huzzah32 board via the I2C bus. 

OLED Display: Utilizes the OLED FeatherWing to deliver visual output, showing information such as date, time, temperature, humidity, and access period details. 

NeoPixel LEDs: The NeoPixel FeatherWing displays visual indicators reflecting the system's status. The LEDs change color according to temperature, with blue indicating 20°C and red representing 35°C. 

MQTT Broker: The system connects to the public Hive MQTT broker at "broker.hivemq.com" for message exchange between the publisher and subscriber. 

**System Workflow:** 

1. Initialization: Establishes WiFi connection, registers with the MQTT broker, and subscribes to relevant MQTT topics. 
1. Sensor Readings and Visual Output: Retrieves sensor data from the BME680 sensor, displaying it on the OLED display along with the date, time, and access period information. NeoPixel LEDs indicate the temperature range with varying colors. 
1. Access Period Handling: Monitors MQTT messages and sets the start and end times of an access period upon receiving "enter" and "exit" messages. Associates user codes with access periods. Logs temperature and humidity data during active periods. 
1. Data Logging: Saves logged data, including temperature, humidity, user code, and timestamps, to a CSV file named "bme680\_data.csv" at the end of each access period. 
1. System Termination: Continuously loops through the workflow until the "C" button on the OLED FeatherWing is pressed. Turns off NeoPixel LEDs and clears the OLED display. 

**Access Period Management:** 

The MQTT subscriber system is designed to manage access periods. An access period represents a specific time duration during which a user enters and exits a particular area. The system handles the start and end times of an access period, as well as the associated user code. 

Start Time: When an "enter" message is received on the MQTT topic "uos/cet235-bi10sg/door/enter", the system captures the message's timestamp and sets it as the start time of the access period. This start time is then used to calculate the elapsed time during the active period. 

End Time: Similarly, when an "exit" message is received on the MQTT topic "uos/cet235- bi10sg/door/exit", the system captures the message's timestamp and sets it as the end time of the access period. The end time marks the termination of the access period. 

User Code: The MQTT topic "uos/cet235-bi10sg/door/user" is used to receive the user code associated with the access period. When a user code message is received, the system associates it with the current access period. 

During an active access period, the system logs temperature and humidity data to a pandas DataFrame. The logged data includes the user code, timestamp, temperature (in degrees Celsius), and humidity (as a percentage). At the end of each access period, the system appends the logged data to the CSV file "bme680\_data.csv" using pandas' to\_csv() method. 

**Visualization and User Interface:** 

OLED Display: The OLED FeatherWing display presents real-time information, including date, time, temperature, humidity, and access period details. The OLED display updates dynamically based on system activities. 

NeoPixel LEDs: The NeoPixel FeatherWing provides visual indicators with color changes representing the temperature range, ranging from blue (20°C) to red (35°C). 

**Data Management and Analysis:** 

The MQTT subscriber system incorporates data management and analysis capabilities. 

Temperature and Humidity Data Logging: During an active access period, the system logs temperature and humidity data to a pandas DataFrame. The logged data includes the user code, timestamp, temperature, and humidity. At the end of each access period, the system saves the logged data to a CSV file named "bme680\_data.csv". If the CSV file already exists, the new data is appended to it. 

Data Analysis: By accumulating data in the CSV file, the system enables further analysis and insights. The stored data can be loaded into pandas DataFrames or other data analysis tools to perform statistical calculations, generate visualizations, or identify patterns and trends over time. 

