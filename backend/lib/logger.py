import datetime
import colorama


def log(level, *args):
    """Log a message with a timestamp and colored prefix."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = " ".join(str(arg) for arg in args)
    prefix = ""
    color = colorama.Style.RESET_ALL

    if level == "debug":
        prefix = "[DEBUG]"
        color = colorama.Fore.CYAN
    elif level == "info":
        prefix = "[INFO]"
        color = colorama.Fore.BLUE
    elif level == "success":
        prefix = "[SUCCESS]"
        color = colorama.Fore.GREEN
    elif level == "warning":
        prefix = "[WARNING]"
        color = colorama.Fore.YELLOW
    elif level == "error":
        prefix = "[ERROR]"
        color = colorama.Fore.RED

    print(
        f"{color}[{colorama.Fore.WHITE}{timestamp}{color}] {prefix} {msg}{colorama.Style.RESET_ALL}"
    )
