def generate_room_layout(filename="room_layout.txt"):
    room_layout = [
        # Górna ściana
        ["W"] * 50,
        # Wiersze wewnętrzne z otwartą przestrzenią i ścianami
        *[
            ["W"] + ["O"] * 48 + ["W"]
            for _ in range(10)
        ],
        # Przykładowy obszar z przeszkodami w środku
        *[
            ["W"] + ["O"] * 10 + ["W"] * 2 + ["O"] * 24 + ["W"] * 2 + ["O"] * 10 + ["W"]
            for _ in range(5)
        ],
        # Środkowa część z większą liczbą przejść
        *[
            ["W"] + ["O"] * 48 + ["W"]
            for _ in range(5)
        ],
        # Wiersze z wyjściami
        ["W"] + ["O"] * 5 + ["E"] + ["O"] * 42 + ["W"],
        ["W"] * 50,
    ]

   
    with open(filename, "w") as file:
        for row in room_layout:
            file.write(" ".join(row) + "\n")

    print(f"Układ pomieszczenia zapisano do pliku {filename}.")


generate_room_layout()
