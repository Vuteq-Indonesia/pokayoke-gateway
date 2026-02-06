PLC_REGISTERS = {
    "A": [
        {
            "code": f"A{i}",
            "reg": (
                "D100" if i in [4, 6]
                else "D102" if i in [20, 18]
                else "D140" if i in [7, 5]
                else "D142" if i in [21, 19]
                else "D144" if i in [3]
                else "D146" if i in [17]
                else "D148" if i in [2, 1]
                else "D150" if i in [15, 16]
                else None
            ),
            "button": (
                "D1000" if i in [4, 6]
                else "D1002" if i in [20, 18]
                else "D1100" if i in [7, 5]
                else "D1102" if i in [21, 19]
                else "D1104" if i in [3]
                else "D1106" if i in [17]
                else "D1108" if i in [2, 1]
                else "D1110" if i in [15, 16]
                else None
            ),
            "lamp": (
                "D1010" if i in [4, 6]
                else "D1012" if i in [20, 18]
                else "D1101" if i in [7, 5]
                else "D1103" if i in [21, 19]
                else "D1105" if i in [3]
                else "D1107" if i in [17]
                else "D1109" if i in [2, 1]
                else "D1111" if i in [15, 16]
                else None
            ),
        }
        for i in range(1, 51)
    ],
    "B": [
        {
            "code": f"B{i}",
            "reg": (
                "D104" if i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 19, 20, 21, 22, 23, 24, 25, 33, 34]
                else "D152" if i in [10, 11, 12, 13, 14, 15, 16, 17, 18, 26, 27, 28, 29, 30, 31, 32]
                else None
            ),
            "button": (
                "D1004" if i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 19, 20, 21, 22, 23, 24, 25, 33, 34]
                else "D1202" if i in [10, 11, 12, 13, 14, 15, 16, 17, 18, 26, 27, 28, 29, 30, 31, 32]
                else None
            ),
            "lamp": (
                "D1014" if i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 19, 20, 21, 22, 23, 24, 25, 33, 34]
                else "D1206" if i in [10, 11, 12, 13, 14, 15, 16, 17, 18, 26, 27, 28, 29, 30, 31, 32]
                else None
            ),
        }
        for i in range(1, 51)
    ],
    "C": [
        {"code": f"C{i}", "reg": "D107", "button": "D1007", "lamp": "D1017"}
        for i in range(1, 51)
    ],
    "D": [
        {"code": f"D{i}", "reg": "D110", "button": "D1020", "lamp": "D1030"}
        for i in range(1, 51)
    ],
    "E": [
        {"code": f"E{i}", "reg": "D114", "button": "D1024", "lamp": "D1034"}
        for i in range(1, 51)
    ],
    "F": [
        {
            "code": f"F{i}",
            "reg": "D119" if i in [3, 14, 17] else "D117",
            "button": "D1028" if i in [3, 14, 17] else "D1027",
            "lamp": "D1038" if i in [3, 14, 17] else "D1037",
        }
        for i in range(1, 51)
    ],
    "AA": [
        {
            "code": f"AA{i}",
            "reg":(
                "D122" if i in [1,3,5,10]
                else "D180" if i in [2,8,9,6]
                else None
            ) ,
            "button": (
                "D1042" if i in [1,3,5,10]
                else "D1200" if i in [2,8,9,6]
                else None
            ),
            "lamp": (
                "D1052" if i in [1, 3, 5, 10]
                else "D1202" if i in [2, 8, 9, 6]
                else None
            )
        }
        for i in range(1, 51)
        # {"code": f"AA{i}", "reg": "D122", "button": "D1042", "lamp": "D1052"}
    ],
    "AB": [
        {
            "code": f"AB{i}",
            "reg": (
                "D124" if i in [1, 2]
                else "D1044" if i in [3]
                else None
            ),
            "button": (
                "D1044" if i in [1, 2]
                else "D1204" if i in [3]
                else None
            ),
            "lamp": (
                "D1054" if i in [1, 2]
                else "D1206" if i in [3]
                else None
            )
        }
        # {"code": f"AB{i}", "reg": "D124", "button": "D1044", "lamp": "D1054"}
        for i in range(1, 51)
    ],
}