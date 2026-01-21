import os
import signal
import time
import msvcrt
import ctypes
import asyncio
from datetime import datetime
import re
import aiohttp
import aiohttp.client_exceptions
import schedule
import keyboard
from colorist import ColorRGB
from colorama import just_fix_windows_console

just_fix_windows_console()

pid = os.getpid()

dirname = os.path.dirname(__file__)

# Change TEST to True if you need to do testing with cabin_ips/test.txt file
TEST = False

if TEST is False:
    d5_d14_plc_ips = os.path.join(dirname, 'plc_ips\\d5_d14_plc_ips.txt')
    d15_slave_plc_ips = os.path.join(dirname, 'plc_ips\\d15_slave_plc_ips.txt')

# FOR TESTING PURPOSES ONLY
if TEST is True:
    d5_d14_plc_ips = os.path.join(dirname, 'plc_ips\\test.txt')
    d15_slave_plc_ips = os.path.join(dirname, 'plc_ips\\test.txt')

CABIN_INFO = os.path.join(dirname, 'plc_ips\\all_cabin_ips.txt')
TIME_SETTINGS_PATH = os.path.join(dirname, 'settings\\time_settings.txt')
ERR_LOGS_PATH = os.path.join(dirname, 'err_logs')

DEFAULT_MORNING_SCHEDULE: str = "07:00"
DEFAULT_AFTERNOON_SCHEDULE: str = "12:00"
DEFAULT_NIGHT_SCHEDULE: str = "19:00"

heartbeat: str = None

morning_schedule: str = None
afternoon_schedule: str = None
night_schedule: str = None

current_lights: str = None
upcoming_lights: str = None
last_change_time: str = None

cabins_list: list[str] = []
ip_list_formatted: list[str] | Exception = []
corridor_lights_change_ok: list[str] = []
corridor_lights_change_err: list[str | type[Exception]] = []
light_options: list[str] = []
custom_time_options: list[str] = []

red = ColorRGB(255, 0, 0)
green = ColorRGB(0, 255, 0)
blue = ColorRGB(13, 94, 175)
cyan = ColorRGB(0, 255, 255)
yellow = ColorRGB(229, 229, 16)
pink = ColorRGB(255, 100, 64)
pink_text = ColorRGB(255, 182, 193)
purple = ColorRGB(128, 0, 128)
RESET = ColorRGB.OFF


def disable_quickedit():
    """
    Disable quickedit mode on Windows terminal. quickedit prevents script to
    run without user pressing keys
    """
    if not os.name == 'posix':
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            device = r'\\.\CONIN$'
            with open(device, 'r', encoding='utf-8') as con:
                h_con = msvcrt.get_osfhandle(con.fileno())
                kernel32.SetConsoleMode(h_con, 0x0080)
        except Exception as e:
            print(f'{red}[SYS ERR]:{RESET} Cannot disable QuickEdit mode ' + str(e))
            print(f'{yellow}[SYS INFO]:{RESET} The script might be automatically\
            paused on Windows terminal')


disable_quickedit()


def time_settings():
    """
        | Opens 'time_settings.txt' file and reads custom given time if there's any,
        | otherwise it writes default time from constant variables
    """
    global morning_schedule
    global afternoon_schedule
    global night_schedule

    with open(TIME_SETTINGS_PATH, "r", encoding='utf-8') as f:
        f_content = f.readlines()
        if f_content:
            while True:
                morning_schedule = f_content[0].strip()
                afternoon_schedule = f_content[1].strip()
                night_schedule = f_content[2].strip()
                break
        else:
            morning_schedule = DEFAULT_MORNING_SCHEDULE
            afternoon_schedule = DEFAULT_AFTERNOON_SCHEDULE
            night_schedule = DEFAULT_NIGHT_SCHEDULE


time_settings()


def load_all_cabins():
    """
        Load all cabin numbers and ips into an array
    """
    with open(CABIN_INFO, "r", encoding="utf-8") as f:
        f_content = f.read()
        for cabin in f_content.splitlines():
            cabins_list.append(cabin)


load_all_cabins()


def show_light_options_menu():
    """
        Shows light colors menu
    """
    global light_options
    light_options = [
        f"1. {pink_text}Pink{RESET}",
        f"2. {blue}Blue{RESET}",
        f"3. {purple}Purple{RESET}",
        f"4. {red}Red{RESET}",
        "5. Exit"
    ]


show_light_options_menu()


def show_time_schedule_menu():
    """
        Shows time schedule menu
    """
    global custom_time_options
    custom_time_options = [
        f"1. {pink_text}Morning   ({morning_schedule} - {afternoon_schedule}){RESET}",
        f"2. {blue}Afternoon ({afternoon_schedule} - {night_schedule}){RESET}",
        f"3. {purple}Night     ({night_schedule} - {morning_schedule}){RESET}",
        "4. Exit"
    ]


show_time_schedule_menu()


def clear_console():
    """
        Clears all console text
    """
    os.system("cls||clear")  # nosec


def show_time(print_time: bool) -> str:
    """Checks current local time and returns it

    Returns:
        str: current local time
    """
    t = time.time()
    now = time.strftime("%H:%M", time.localtime(t))
    if print_time is True:
        print(f"\nCurrent time: {yellow}{now}{RESET}\n")
    return now


def show_date(print_date: bool) -> str:
    """Checks current datetime and returns it

    Returns:
        str: current datetime
    """
    now = datetime.today().strftime('%Y-%m-%d %H-%M-%S')
    if print_date is True:
        print(f"\nCurrent date: {yellow}{now}{RESET}\n")
    return now


def err_handler(e: Exception | str):
    """
    | When an error is encountered, it will write all errors in a txt file,
    | then call func to restart all required tasks for TAR clock in and out to work properly.

    Args:
        e (Exception | str): any error exception
    """
    err_time_now = show_time(False)
    err_date_now = show_date(False)
    try:
        with open(f"{ERR_LOGS_PATH}\\{err_date_now} - err_log.txt", "w", encoding="utf-8") as f:
            f.write(f"DATE & TIME: {err_date_now}\n")
            f.write("--------------------------------\n")
            f.write(f"[ERR]: {str(e)}")
        print(f"{red}-----------------------------------------------------------{RESET}")
        print(f"{red}<<< FATAL ERROR HAS OCCURED - SCRIPT WILL BE TERMINATED >>>{RESET}")
        print(f"{red}-----------------------------------------------------------{RESET}\n")
        print(f"{err_time_now} - {cyan}ERROR LOGS CREATED >{RESET} {yellow}{ERR_LOGS_PATH}\\{err_date_now} - err_log.txt{RESET}")
        print(f"\n{yellow}-----------------------------{RESET}")
        print(f"{cyan}[SYS INFO]:{RESET} {yellow}SCRIPT TERMINATED{RESET}")
        print(f"{yellow}-----------------------------{RESET}")
        os.system("pause")  # nosec
        os.kill(pid, signal.SIGTERM)
    except FileNotFoundError as be:
        print(f"{err_time_now} - {red}{be}{RESET}")
        os.makedirs(ERR_LOGS_PATH)
        print(f"{err_time_now} - {cyan}[SYS INFO]: ERR_LOGS FOLDER CREATED{RESET}")
        time.sleep(5)
        err_handler(e)
    print(f"{err_time_now} - {red}[ERR]: {e}{RESET}")


def display_manual_menu(menu: list[str], option: int):
    """
        Creates [X] check box next to each light color row
    """
    for number, item in enumerate(menu, 1):
        if number == option:
            print(f'[{yellow}X{RESET}]', item)
        else:
            print('[ ]', item)


def display_invalid_input_err():
    """
        Prints invalid input err message
    """
    print(f"\n{red}-------------{RESET}")
    print(f"{red}INVALID INPUT{RESET}")


def display_ver():
    """
        Prints title and ver
    """
    print(f"{cyan}< Corridor Light Controller - Ver 2.4 >{RESET}\n")


def display_current_settings():
    """
        Displays current settings for time and colors in a table like format
    """
    print(f"\n{yellow}Current settings for time & light color:{RESET}")
    print("----------------------------------------")
    print(f"- {morning_schedule} > {pink_text}Pink{RESET}   | {red}R{RESET}: 255 {green}G{RESET}: 100 {blue}B{RESET}: 64")  # noqa: F821
    print(f"- {afternoon_schedule} > {blue}Blue{RESET}   | {red}R{RESET}: 13  {green}G{RESET}: 94  {blue}B{RESET}: 175")  # noqa: F821
    print(f"- {night_schedule} > {purple}Purple{RESET} | {red}R{RESET}: 128 {green}G{RESET}: 0   {blue}B{RESET}: 128")  # noqa: F821
    print("----------------------------------------")


def display_keyboard_legend():
    """
        Prints Keyboard menu legend
    """
    print(f"\n{yellow}Keyboard menu:{RESET}")
    print("--------------------------")
    print(f"- Change time schedule {yellow}[T]{RESET}")
    print(f"- Manual light change  {yellow}[C]{RESET}")
    print(f"- Terminate script     {yellow}[Q]{RESET}")
    print("--------------------------\n")


def display_auto_lights_mode_running_info():
    """
        Prints auto light changer running info
    """
    print(f"{cyan}AUTOMATIC LIGHT CHANGER IS RUNNING{RESET}")
    print(f"{cyan}----------------------------------{RESET}")
    display_upcoming_schedule()


def display_upcoming_schedule():
    """
        | Prints additional info about current lights and when was it changed,
        | as well as the upcoming light and the time when the change will occur
    """
    global current_lights
    global upcoming_lights
    global last_change_time

    upcoming_time: str = None
    t = time.time()
    now_int = int(time.strftime("%H%M", time.localtime(t)))

    morning_schedule_hm = morning_schedule.split(":")
    afternoon_schedule_hm = afternoon_schedule.split(":")
    night_schedule_hm = night_schedule.split(":")

    morning_schedule_hm_int = int(morning_schedule_hm[0] + morning_schedule_hm[1])
    afternoon_schedule_hm_int = int(afternoon_schedule_hm[0] + afternoon_schedule_hm[1])
    night_schedule_hm_int = int(night_schedule_hm[0] + night_schedule_hm[1])

    if morning_schedule_hm_int <= now_int < afternoon_schedule_hm_int:
        current_lights = f"{pink_text}[PINK]{RESET}"
        upcoming_lights = f"{blue}[BLUE]{RESET}"
        upcoming_time = f"{yellow}[{afternoon_schedule}]{RESET}"
        if last_change_time is None:
            last_change_time = morning_schedule
    elif afternoon_schedule_hm_int <= now_int < night_schedule_hm_int:
        current_lights = f"{blue}[BLUE]{RESET}"
        upcoming_lights = f"{purple}[PURPLE]{RESET}"
        upcoming_time = f"{yellow}[{night_schedule}]{RESET}"
        if last_change_time is None:
            last_change_time = afternoon_schedule
    else:
        current_lights = f"{purple}[PURPLE]{RESET}"
        upcoming_lights = f"{pink_text}[PINK]{RESET}"
        upcoming_time = f"{yellow}[{morning_schedule}]{RESET}"
        if last_change_time is None:
            last_change_time = night_schedule

    print(f"- Current lights were changed at {yellow}[{last_change_time}]{RESET} to {current_lights}")
    print(f"- Next light change will trigger at {upcoming_time} to {upcoming_lights}\n")


async def getter(url: str, session: aiohttp.ClientSession):
    """
        | Getter for sending request to the server for given ip,
        | which triggers light color change depending on the given URL
        | If response is 200, URL string will be appended to the list for successful changes,
        | else will prompt an error string and appended it to err list as well as timeout
    """
    try:
        async with session.get(url=url, timeout=10) as response:
            await response.read()
            if response.status == 200:
                corridor_lights_change_ok.append(url)
            else:
                corridor_lights_change_err.append(url)
    except TimeoutError as e:
        corridor_lights_change_err.append(url)
        print(f"Unable to get url {url} due to {e.__class__}.".format())


async def setter(urls: str):
    """
        A setter for making a tuple for all ip addresses and passing them to getter func
    """
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(getter(url, session) for url in urls))


def d15_red_lights_slaves():
    """
        | Red color for master-slave PLCs on deck 15 \n
        | DB6000.71 - Red (1000)
        | DB6000.72 - Green (0)
        | DB6000.73 - Blue (0)
    """
    with open(d15_slave_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.71,d=1000&PDP,,DB6000.72,d=0&PDP,,DB6000.73,d=0")


def d15_blue_lights_slaves():
    """
        | Blue color for master-slave PLCs on deck 15 \n
        | DB6000.71 - Red (0)
        | DB6000.72 - Green (0)
        | DB6000.73 - Blue (1000)
    """
    with open(d15_slave_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.71,d=0&PDP,,DB6000.72,d=0&PDP,,DB6000.73,d=1000")


def d15_purple_lights_slaves():
    """
        | Purple color for master-slave PLCs on deck 15 \n
        | DB6000.71 - Red (502)
        | DB6000.72 - Green (0)
        | DB6000.73 - Blue (502)
    """
    with open(d15_slave_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.71,d=502&PDP,,DB6000.72,d=0&PDP,,DB6000.73,d=502")


def d15_pink_lights_slaves():
    """
        | Pink color for master-slave PLCs on deck 15,
        | calls d15 func after for loop and then triggers all lights to change \n
        | DB6000.71 - Red (1000)
        | DB6000.72 - Green (502)
        | DB6000.73 - Blue (251)
    """
    with open(d15_slave_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.71,d=1000&PDP,,DB6000.72,d=502&PDP,,DB6000.73,d=251")


def red_lights():
    """
        | Red color for master PLCs on all decks except d15,
        | calls d15 func after for loop and then triggers all lights to change \n
        | DB6000.76 - Red (1000)
        | DB6000.77 - Green (0)
        | DB6000.78 - Blue (0)
    """
    with open(d5_d14_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.76,d=1000&PDP,,DB6000.77,d=0&PDP,,DB6000.78,d=0")
    d15_red_lights_slaves()
    exec_light_change()


def blue_lights():
    """
        | Blue color for master PLCs on all decks except d15,
        | calls d15 func after for loop and then triggers all lights to change \n
        | DB6000.76 - Red (0)
        | DB6000.77 - Green (0)
        | DB6000.78 - Blue (1000)
    """
    with open(d5_d14_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.76,d=0&PDP,,DB6000.77,d=0&PDP,,DB6000.78,d=1000")
    d15_blue_lights_slaves()
    exec_light_change()


def purple_lights():
    """
        | Purple color for master PLCs on all decks except d15,
        | calls d15 func after for loop and then triggers all lights to change \n
        | DB6000.76 - Red (502)
        | DB6000.77 - Green (0)
        | DB6000.78 - Blue (502)
    """
    with open(d5_d14_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.76,d=502&PDP,,DB6000.77,d=0&PDP,,DB6000.78,d=502")
    d15_purple_lights_slaves()
    exec_light_change()


def pink_lights():
    """
        | Pink color for master PLCs on all decks except d15,
        | calls d15 func after for loop and then triggers all lights to change \n
        | DB6000.76 - Red (1000)
        | DB6000.77 - Green (502)
        | DB6000.78 - Blue (251)
    """
    with open(d5_d14_plc_ips, "r", encoding="utf-8") as f:
        f_content = f.read()
        for ip in f_content.splitlines():
            ip_list_formatted.append(f"http://{ip}/setValues.exe?PDP,,DB6000.76,d=1000&PDP,,DB6000.77,d=502&PDP,,DB6000.78,d=251")
    d15_pink_lights_slaves()
    exec_light_change()


def is_time_format_correct(time_input: str):
    """
        Checks if inserted time format from user is valid, returns true or false
    """
    time_format = "%H:%M"
    try:
        time.strptime(time_input, time_format)
        return True
    except ValueError:
        return False


def manual_time_change():
    """
        Display menu for manually changing time
    """
    def manual_mode_info():
        print(f"{yellow}----------------------{RESET}")
        print(f"{yellow}MANUAL TIME SCHEDULING{RESET}")
    err = False
    while True:
        clear_console()
        manual_mode_info()
        if err is True:
            display_invalid_input_err()
            print(f"{yellow}Time must be between \"00:00 - 23:59\"{RESET}\n")
            err = False
        selected_option = 0
        show_time(True)
        display_manual_menu(custom_time_options, selected_option)
        try:
            input_time = ""
            exit_choice = ""
            new = int(input("\nSelect a schedule:\n>> "))
            selected_option = new
            clear_console()
            manual_mode_info()
            show_time(True)
            display_manual_menu(custom_time_options, selected_option)
            match selected_option:
                case 1:
                    print(f"\n{pink_text}-----------------------------{RESET}")
                    input_time = str(input("Insert new time for " + f"{pink_text}[MORNING]{RESET}:\n>> ")).lower()
                case 2:
                    print(f"\n{blue}-------------------------------{RESET}")
                    input_time = str(input("Insert new time for " + f"{blue}[AFTERNOON]{RESET}:\n>> ")).lower()
                case 3:
                    print(f"\n{purple}---------------------------{RESET}")
                    input_time = str(input("Insert new time for " + f"{purple}[NIGHT]{RESET}:\n>> ")).lower()
                case 4:
                    print("\n-----------------------")
                    exit_choice = str(input("Exit manual mode? [Y/n]\n>> ")).lower()
                case _:
                    err = True
                    continue

            if input_time:
                is_valid = is_time_format_correct(input_time)
                if is_valid is True:
                    time_change(selected_option, input_time)
                    continue
                if is_valid is False:
                    err = True
                    continue

            if exit_choice in ("n", "no"):
                selected_option = 0
                continue
            if exit_choice in ("y", "yes", ""):
                main()
            else:
                err = True
                continue

        except ValueError:
            err = True
            continue
        break


def time_change(option: int, input_time: str):
    """
        Calls time functions based on user input respectively
    """
    match option:
        case 1:
            morning_time_change(input_time)
        case 2:
            afternoon_time_change(input_time)
        case 3:
            night_time_change(input_time)
        case 4:
            main()


def morning_time_change(input_time):
    """
        Writes custom given time into 'time_settigs.txt', file and overrides global morning schedule var
    """
    global morning_schedule
    with open(TIME_SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(f"{input_time}\n{afternoon_schedule}\n{night_schedule}")
    morning_schedule = f"{input_time}"
    show_time_schedule_menu()
    display_auto_lights_mode_running_info()
    main()


def afternoon_time_change(input_time):
    """
        Writes custom given time into 'time_settigs.txt' file and overrides global afternoon schedule var
    """
    global afternoon_schedule
    with open(TIME_SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(f"{morning_schedule}\n{input_time}\n{night_schedule}")  # noqa: F821
    afternoon_schedule = f"{input_time}"
    show_time_schedule_menu()
    display_auto_lights_mode_running_info()
    main()


def night_time_change(input_time):
    """
        Writes custom given time into 'time_settigs.txt' file and overrides global night schedule var
    """
    global night_schedule
    with open(TIME_SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(f"{morning_schedule}\n{afternoon_schedule}\n{input_time}")  # noqa: F821
    night_schedule = f"{input_time}"
    show_time_schedule_menu()
    display_auto_lights_mode_running_info()
    main()


def manual_light_change():
    """
        Menu display for manual time change at any given time by the user
    """
    def manual_mode_info():
        print(f"{yellow}------------------------------{RESET}")
        print(f"{yellow}MANUAL CORRIDOR LIGHTS CHANGES{RESET}")
    err = False
    while True:
        clear_console()
        manual_mode_info()
        if err is True:
            display_invalid_input_err()
            err = False
        selected_option = 0
        show_time(True)
        display_manual_menu(light_options, selected_option)
        try:
            choice = ""
            new = int(input("\nSelect light color:\n>> "))
            selected_option = new
            clear_console()
            manual_mode_info()
            show_time(True)
            display_manual_menu(light_options, selected_option)
            match selected_option:
                case 1:
                    print(f"\n{pink_text}------------------------------------------{RESET}")
                    choice = str(input("Corridor lights will be changed to: " + f"{pink_text}[PINK]{RESET}" + "\nContinue? [Y/n]\n>> ")).lower()
                case 2:
                    print(f"\n{blue}------------------------------------------{RESET}")
                    choice = str(input("Corridor lights will be changed to: " + f"{blue}[BLUE]{RESET}" + "\nContinue? [Y/n]\n>> ")).lower()
                case 3:
                    print(f"\n{purple}--------------------------------------------{RESET}")
                    choice = str(input("Corridor lights will be changed to: " + f"{purple}[PURPLE]{RESET}" + "\nContinue? [Y/n]\n>> ")).lower()
                case 4:
                    print(f"\n{red}-----------------------------------------{RESET}")
                    choice = str(input("Corridor lights will be changed to: " + f"{red}[RED]{RESET}" + "\nContinue? [Y/n]\n>> ")).lower()
                case 5:
                    print("\n-----------------------")
                    choice = str(input("Exit manual mode? [Y/n]\n>> ")).lower()
                case _:
                    err = True
                    continue

            if choice in ("n", "no"):
                selected_option = 0
                continue
            if choice in ("y", "yes", ""):
                light_change(selected_option)
            else:
                err = True
                continue

        except ValueError:
            err = True
            continue
        break


def exec_light_change():
    """
        Main function that triggers all the lights to change by setting all ip addresses from txt file
    """
    global last_change_time
    try:
        print(f"\n{yellow}--------------------------{RESET}")
        print(f"{yellow}<<< PROCESSING CHANGES >>>{RESET}")
        print(f"{yellow}--------------------------{RESET}\n")
        start = time.time()
        asyncio.run(setter(ip_list_formatted))
        end = time.time()
        total_time = end - start
        light_change_ok = len(corridor_lights_change_ok)
        light_change_err = len(corridor_lights_change_err)
        clear_console()
        if light_change_err == 0:
            print(f"{green}-----------------------------------------------------------------{RESET}")
            print(f"{green}>>> [SUCCESS]:{RESET} All corridor lights have been {green}successfully{RESET} changed")
            print(f"{green}-----------------------------------------------------------------{RESET}")
            light_execution_status(light_change_ok, light_change_err, total_time)
        elif light_change_ok == 0:
            print(f"{red}------------------------------------------------------------{RESET}")
            print(f"{red}>>> [FATAL ERROR]:{RESET} All corridor lights have failed to {red}change{RESET}")
            print(f"{red}------------------------------------------------------------{RESET}")
            print("\n")
            print(f"{red}>>>{RESET} Failed to change {red}{light_change_err}{RESET} corridor lights:")
            print(f"{red}---------------------------------------{RESET}")
            failed_cabin_lights(corridor_lights_change_err)
            light_execution_status(light_change_ok, light_change_err, total_time)
        elif light_change_err > 0:
            print(f"{yellow}-----------------------------------------------------{RESET}")
            print(f"{yellow}>>> [WARNING]:{RESET} Some corridor lights have been {yellow}changed{RESET}")
            print(f"{yellow}-----------------------------------------------------{RESET}")
            print("\n")
            print(f"{red}>>>{RESET} Failed to change {red}{light_change_err}{RESET} corridor lights:")
            print(f"{red}---------------------------------------{RESET}")
            failed_cabin_lights(corridor_lights_change_err)
            light_execution_status(light_change_ok, light_change_err, total_time)
        ip_list_formatted.clear()
        corridor_lights_change_err.clear()
        corridor_lights_change_ok.clear()
        last_change_time = show_time(False)
        display_auto_lights_mode_running_info()
        display_keyboard_legend()
        show_time(True)
    except Exception as e:
        err_handler(e)


def failed_cabin_lights(light_change_err: list[str]):
    """
        | Extracts IP from the PLC URL and iterates in the list to find the cooresponding
        | cabin number with the associated PLC IP
    Args:
        light_change_err (list[str]): array of failed cabin URLs
    """
    reg_pattern = r'.*?\/{2}(.*)\/.*'
    for failed in light_change_err:
        match = re.search(reg_pattern, failed)
        failed_ip = match.group(1)
        for cabin in cabins_list:
            if failed_ip in cabin:
                print(f"{red}>{RESET} {cabin}")


def light_execution_status(light_change_ok: int, light_change_err: int, total_time: int):
    """
        Prints final status of light changes
    Args:
        light_change_ok (int): lights that successfully changed
        light_change_err (int): lights that failed to change
        total_time (int): total time it took to run all lights change
    """
    total_cabins = light_change_ok + light_change_err
    print("\n")
    print(f"{yellow}>>>{RESET} Corridor lights status:")
    print(f"{yellow}---------------------------{RESET}")
    print(f"Changed: {green}{light_change_ok}{RESET}")
    print(f"Failed:  {red}{light_change_err}{RESET}")
    print(f"Total:   {cyan}{total_cabins}{RESET}")
    print(f"Time:    {yellow}{total_time:.2f}s{RESET}")
    print(f"{yellow}---------------------------{RESET}")
    print("\n")


def light_change(option: int):
    """
        Light change triggers based on user input
    """
    match option:
        case 1:
            pink_lights()
        case 2:
            blue_lights()
        case 3:
            purple_lights()
        case 4:
            red_lights()
        case 5:
            main()
        case _:
            print(f"\n{red}There was an error in light_change func{RESET}")


def scheduler():
    """
        Schedules parallel execution for light changing functions at given times
    """
    global heartbeat
    if not heartbeat:
        schedule.every().day.at(f"{morning_schedule}").do(pink_lights)  # noqa: F821
        schedule.every().day.at(f"{afternoon_schedule}").do(blue_lights)  # noqa: F821
        schedule.every().day.at(f"{night_schedule}").do(purple_lights)  # noqa: F821
        heartbeat = schedule.every(1).minutes.do(display_main)
    else:
        heartbeat = None
        schedule.clear()
        scheduler()


def display_main():
    """
        Displays all initial info on the main frame
    """
    clear_console()
    display_ver()
    display_auto_lights_mode_running_info()
    display_keyboard_legend()
    display_current_settings()
    show_time(True)


def main():
    """
        Main menu display
    """
    try:
        display_main()
        scheduler()

        while True:
            schedule.run_pending()

            if keyboard.is_pressed("t"):
                manual_time_change()

            if keyboard.is_pressed("c"):
                manual_light_change()

            if keyboard.is_pressed("q"):
                print(f"{cyan}[SYS INFO]:{RESET} {yellow}SCRIPT TERMINATED{RESET}")
                os.system("pause")  # nosec
                os.kill(pid, signal.SIGTERM)

    except Exception as e:
        err_handler(e)


main()
