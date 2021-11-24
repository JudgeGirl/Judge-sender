from dataclasses import dataclass


@dataclass
class Const:
    WT: int = 0
    CE: int = 1
    OLE: int = 2
    MLE: int = 3
    RE: int = 4
    TLE: int = 5
    WA: int = 6
    AC: int = 7
    PE: int = -1
    res: tuple = (
        "Waiting",
        "Compilation Error",
        "Output Limit Exceeded",
        "Memory Limit Exceeded",
        "Runtime Error",
        "Time Limit Exceeded",
        "Wrong Answer",
        "Accepted",
    )
    lng: tuple = ("*", "C99", "C++98", "C# 3.0", "Python 3", "Scala 2")


const = Const()
