import machine, utime


def blink(number_of_blinks=1, speed="normal"):
    if speed == "fast":
        sleep_time = 0.25
    elif speed == "slow":
        sleep_time = 1
    else:
        sleep_time = 0.5

    LED = machine.Pin("LED", machine.Pin.OUT)
    LED.value(0)
    for _ in range(number_of_blinks):
        LED.value(1)
        utime.sleep(sleep_time)
        LED.value(0)
        utime.sleep(sleep_time)
    LED.off()
