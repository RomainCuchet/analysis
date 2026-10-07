import pandas as pd
import matplotlib.pyplot as plt


def charger_resultats(path):
    """
    Charge le fichier généré par le benchmark.

    Retourne un DataFrame avec les colonnes :
        taille_Ko
        temps_seq
        temps_par
        acceleration
        coeurs
        result
        valide
    """
    lignes = []

    with open(path, "r") as f:
        for ligne in f:
            ligne = ligne.strip()

            if not ligne:
                continue

            morceaux = ligne.split()

            if len(morceaux) >= 8:
                try:
                    taille = float(morceaux[0])
                    seq = float(morceaux[1])
                    par = float(morceaux[2])
                    acceleration = float(morceaux[3])
                    coeurs = int(morceaux[4])
                    result = float(morceaux[5])

                    valide = morceaux[-1].lower() == "true"

                    lignes.append([
                        taille,
                        seq,
                        par,
                        acceleration,
                        coeurs,
                        result,
                        valide
                    ])

                except ValueError:
                    pass

    return pd.DataFrame(
        lignes,
        columns=[
            "taille_Ko",
            "temps_seq",
            "temps_par",
            "acceleration",
            "coeurs",
            "result",
            "valide"
        ]
    )


def _filtrer_threads(df, threads):
    """
    Filtre le DataFrame sur les nombres de threads demandés.

    Si threads est None, toutes les valeurs sont conservées.
    """
    if threads is None:
        return df

    return df[df["coeurs"].isin(threads)]


def _afficher_lignes_caches(ax, caches=None):
    """
    Affiche les tailles de cache sous forme de lignes verticales.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axe sur lequel dessiner les lignes.
    caches : dict, optional
        Dictionnaire associant le nom du cache à sa taille en Ko.

        Exemple :
            {"L1": 32, "L2": 256, "L3": 8192, "L3-2": 8192}

    Les étiquettes sont placées directement à côté des lignes verticales,
    et non dans une légende.
    """
    if not caches:
        return

    couleurs = ["red", "blue", "green", "orange", "purple", "brown"]

    for i, (nom, valeur) in enumerate(caches.items()):
        if valeur is None:
            continue

        couleur = couleurs[i % len(couleurs)]

        ax.axvline(
            valeur,
            color=couleur,
            linestyle="--",
            linewidth=1.2,
            alpha=0.8,
            zorder=1
        )

        # Étiquette directement associée à la ligne, légèrement décalée
        # pour rester lisible et éviter une légende supplémentaire.
        ax.annotate(
            f"{nom} = {valeur:g} Ko",
            xy=(valeur, 1),
            xycoords=("data", "axes fraction"),
            xytext=(5, -5 - (i % 2) * 18),
            textcoords="offset points",
            rotation=90,
            rotation_mode="anchor",
            va="top",
            ha="left",
            fontsize=9,
            color=couleur,
            fontweight="medium",
            bbox=dict(
                boxstyle="round,pad=0.18",
                facecolor="white",
                edgecolor="none",
                alpha=0.75
            ),
            clip_on=False
        )


from pathlib import Path
import matplotlib.pyplot as plt


def afficher_acceleration_vs_coeurs(
    path,
    taille_ko=None,
    threads=None,
    caches=None
):
    """
    Affiche l'accélération en fonction du nombre de threads.

    Paramètres
    ----------
    path : str, Path ou list[str | Path]
        Chemin vers un fichier de résultats ou liste de chemins.
        Une courbe est tracée pour chaque fichier.

    taille_ko : float, optionnel
        Taille des données à afficher.
        Par défaut : plus grande taille disponible dans chaque fichier.

    threads : list[int], optionnel
        Liste des nombres de threads à afficher.
        Par défaut : tous les threads disponibles.

    caches : dict, optionnel
        Dictionnaire associant le nom de chaque cache à sa taille en Ko.
        Exemple : {"L1": 32, "L2": 256, "L3": 8192}

        Ces paramètres ne sont pas représentés sur ce graphique
        car l'axe X correspond au nombre de threads et non à la
        taille des données.
    """

    # Accepte un seul path ou une liste de paths
    if isinstance(path, (str, Path)):
        paths = [path]
    else:
        paths = path

    fig, ax = plt.subplots()

    for p in paths:
        df = charger_resultats(p)

        if df.empty:
            print(f"Aucune donnée trouvée dans {p}.")
            continue

        # Taille par défaut : plus grande taille disponible
        taille = taille_ko
        if taille is None:
            taille = df["taille_Ko"].max()

        data = df[df["taille_Ko"] == taille]
        data = _filtrer_threads(data, threads)

        if data.empty:
            print(
                f"Aucune donnée correspondant aux paramètres "
                f"dans {p}."
            )
            continue

        data = data.sort_values("coeurs")

        # Nom utilisé dans la légende
        label = Path(p).stem

        ax.plot(
            data["coeurs"],
            data["acceleration"],
            marker="o",
            label=label
        )

    ax.set_xlabel("Nombre de threads")
    ax.set_ylabel("Accélération")

    if taille_ko is not None:
        ax.set_title(
            f"Accélération en fonction du nombre de threads "
            f"({taille_ko:.0f} Ko)"
        )
    else:
        ax.set_title(
            "Accélération en fonction du nombre de threads"
        )

    ax.grid(True)

    # Afficher la légende uniquement s'il y a plusieurs courbes
    if len(paths) > 1:
        ax.legend()

    fig.tight_layout()
    plt.show()


def afficher_acceleration_vs_taille(
    path,
    coeurs=None,
    threads=None,
    caches=None
):
    """
    Affiche l'accélération en fonction de la taille des données.

    Si coeurs est None, utilise le nombre maximal de threads mesuré.

    threads permet de sélectionner les nombres de threads à considérer.
    Pour cette fonction, si plusieurs threads sont demandés, une courbe
    est créée pour chaque nombre de threads.

    Les tailles de cache sont représentées par des lignes verticales
    sur l'axe des tailles de données.
    """
    df = charger_resultats(path)

    if df.empty:
        print("Aucune donnée trouvée.")
        return

    if threads is not None:
        df = _filtrer_threads(df, threads)

        if df.empty:
            print("Aucune donnée correspondant aux threads demandés.")
            return

    if coeurs is not None:
        threads_a_afficher = [coeurs]
    elif threads is not None:
        threads_a_afficher = sorted(threads)
    else:
        threads_a_afficher = [df["coeurs"].max()]

    fig, ax = plt.subplots()

    for thread in threads_a_afficher:
        data = df[df["coeurs"] == thread].sort_values("taille_Ko")

        if data.empty:
            continue

        ax.plot(
            data["taille_Ko"],
            data["acceleration"],
            marker="o",
            label=f"{thread} threads"
        )

    # Lignes verticales indiquant les tailles des caches
    _afficher_lignes_caches(ax, caches)

    ax.set_xlabel("Taille des données (Ko)")
    ax.set_ylabel("Accélération")

    ax.set_title(
        "Accélération en fonction de la taille"
    )

    ax.set_xscale("log")

    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    plt.show()


def afficher_temps_vs_taille(
    path,
    coeurs=None,
    threads=None,
    caches=None
):
    """
    Compare les temps séquentiel et parallèle en fonction
    de la taille des données.

    Si un seul nombre de threads est utilisé, les temps séquentiel
    et parallèle sont affichés.

    Si plusieurs threads sont fournis via threads, une courbe
    parallèle est affichée pour chaque nombre de threads.

    Les tailles de cache sont représentées par des lignes verticales
    sur l'axe des tailles de données.
    """
    df = charger_resultats(path)

    if df.empty:
        print("Aucune donnée trouvée.")
        return

    if threads is not None:
        df = _filtrer_threads(df, threads)

        if df.empty:
            print("Aucune donnée correspondant aux threads demandés.")
            return

    if coeurs is not None:
        threads_a_afficher = [coeurs]
    elif threads is not None:
        threads_a_afficher = sorted(threads)
    else:
        threads_a_afficher = [df["coeurs"].max()]

    fig, ax = plt.subplots()

    # Temps séquentiel : identique quel que soit le nombre de threads.
    # On ne l'affiche qu'une seule fois.
    data_seq = (
        df.sort_values("taille_Ko")
        .drop_duplicates(subset="taille_Ko")
    )

    ax.plot(
        data_seq["taille_Ko"],
        data_seq["temps_seq"],
        marker="o",
        label="Séquentiel"
    )

    for thread in threads_a_afficher:
        data = df[df["coeurs"] == thread].sort_values("taille_Ko")

        if data.empty:
            continue

        ax.plot(
            data["taille_Ko"],
            data["temps_par"],
            marker="o",
            label=f"Parallèle - {thread} threads"
        )

    # Lignes verticales indiquant les tailles des caches
    _afficher_lignes_caches(ax, caches)

    ax.set_xlabel("Taille des données (Ko)")
    ax.set_ylabel("Temps par élément (s)")

    ax.set_title(
        "Temps d'exécution en fonction de la taille"
    )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    plt.show()


def afficher_acceleration_toutes_tailles(
    path,
    threads=None,
    caches=None
):
    """
    Affiche une courbe d'accélération par nombre de threads.

    threads : list[int], optionnel
        Permet de sélectionner les threads à afficher.

        Exemple :
            threads=[1, 4, 8, 16]

        Si None, tous les threads sont affichés.

    Les tailles de cache sont représentées par des lignes verticales
    sur l'axe des tailles de données.
    """
    df = charger_resultats(path)

    if df.empty:
        print("Aucune donnée trouvée.")
        return

    df = _filtrer_threads(df, threads)

    if df.empty:
        print("Aucune donnée correspondant aux threads demandés.")
        return

    fig, ax = plt.subplots()

    for coeurs, data in df.groupby("coeurs"):
        data = data.sort_values("taille_Ko")

        ax.plot(
            data["taille_Ko"],
            data["acceleration"],
            marker="o",
            label=f"{coeurs} threads"
        )

    # Lignes verticales indiquant les tailles des caches
    _afficher_lignes_caches(ax, caches)

    ax.set_xlabel("Taille des données (Ko)")
    ax.set_ylabel("Accélération")

    ax.set_title(
        "Accélération en fonction de la taille des données"
    )

    ax.set_xscale("log")

    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    plt.show()


def afficher_speedup_ideal(
    path,
    taille_ko=None,
    threads=None,
    caches=None
):
    """
    Compare l'accélération mesurée à l'accélération idéale.

    Idéalement :
        accélération = nombre de threads

    Les tailles de cache ne sont pas représentées sur ce graphique
    car l'axe X correspond au nombre de threads.
    """
    df = charger_resultats(path)

    if df.empty:
        print("Aucune donnée trouvée.")
        return

    if taille_ko is None:
        taille_ko = df["taille_Ko"].max()

    data = df[df["taille_Ko"] == taille_ko]
    data = _filtrer_threads(data, threads)

    if data.empty:
        print("Aucune donnée correspondant aux paramètres.")
        return

    data = data.sort_values("coeurs")

    fig, ax = plt.subplots()

    ax.plot(
        data["coeurs"],
        data["acceleration"],
        marker="o",
        label="Accélération mesurée"
    )

    ax.plot(
        data["coeurs"],
        data["coeurs"],
        linestyle="--",
        label="Accélération idéale"
    )

    ax.set_xlabel("Nombre de threads")
    ax.set_ylabel("Accélération")

    ax.set_title(
        f"Accélération mesurée vs idéale ({taille_ko:.0f} Ko)"
    )

    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    plt.show()


def afficher_temps_sequentiel_vs_taille(
    path,
    caches=None
):
    """
    Affiche le temps séquentiel en fonction de la taille des données.

    Les tailles de cache sont représentées par des lignes verticales
    sur l'axe des tailles de données.

    Paramètres
    ----------
    path : str
        Chemin vers le fichier de résultats.

    caches : dict, optionnel
        Dictionnaire associant le nom de chaque cache à sa taille en Ko.
        Exemple : {"L1": 32, "L2": 256, "L3": 8192, "L3-2": 8192}
    """
    df = charger_resultats(path)

    if df.empty:
        print("Aucune donnée trouvée.")
        return

    # Le temps séquentiel est identique pour chaque nombre de threads.
    # On conserve donc une seule mesure par taille.
    data = (
        df.sort_values("taille_Ko")
        .drop_duplicates(subset="taille_Ko")
    )

    fig, ax = plt.subplots()

    ax.plot(
        data["taille_Ko"],
        data["temps_seq"],
        marker="o",
        label="Temps séquentiel"
    )

    # Lignes verticales indiquant les tailles des caches
    _afficher_lignes_caches(ax, caches)

    ax.set_xlabel("Taille des données (Ko)")
    ax.set_ylabel("Temps séquentiel par élément (s)")

    ax.set_title(
        "Temps séquentiel en fonction de la taille des données"
    )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    plt.show()

# Exemple de dictionnaire de caches :
#
# caches = {
#     "L1": 32,
#     "L2": 256,
#     "L3": 8192,
#     "L3-2": 16384,
# }
#
# Exemple :
# afficher_acceleration_vs_taille(
#     "resultats.txt",
#     coeurs=8,
#     caches=caches
# )
