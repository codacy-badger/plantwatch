OIL = "Mineralölprodukte"
ENERGY_SOURCE = "Energieträger"
YEARLY_PRD = "Jahresproduktion [TWh]"
NETOP = "Nennleistung [GW]"

SORT_CRITERIA_BLOCKS = ([('blockname', 'Name'), ('netpower', 'Nennleistung'),
                        ('initialop', 'Inbetriebnahme')], "netpower")
SORT_CRITERIA_PLANTS = ([('plantname', 'Name'), ('totalpower', 'Gesamtleistung'),
                        ('initialop', 'Inbetriebnahme'), ('latestexpanded',
                        'Zuletzt erweitert'), ('eff', 'Effizienz'),
                        ('workload', 'Auslastung'), ('co2', 'CO2 Ausstoß'),
                        ('energy', 'Energie')], "totalpower")
SORT_CRITERIA_PLANTS_OLD = ([('plantname', 'Name'), ('totalpower', 'Gesamtleistung'),
                            ('initialop', 'Inbetriebnahme'), ('latestexpanded',
                            'Zuletzt erweitert')], "totalpower")


SLIDER_1 = "1950;2025"
SLIDER_2p = "300;4500"
SLIDER_2b = "250;1500"

HOURS_IN_YEAR = 365 * 24



SL_1 = [1950, 2025, 1950, 2025, 5]
SL_2b = [250, 1500, 0, 1500, 250]
SL_2p = [250, 4500, 0, 4500, 250]

HOURS_IN_YEAR = 365 * 24
PRTR_YEARS = list(range(2007, 2019))
ENERGY_YEARS = list(range(2015, 2020))
YEARS = ENERGY_YEARS
YEAR = PRTR_YEARS[-1]
LATEST_YEAR = ENERGY_YEARS[-1]

FULL_HOURS = "Volllaststunden [" + str(YEAR) + "]"

FEDERAL_STATES = ['Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg',
                    'Bremen', 'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern',
                    'Niedersachsen', 'Nordrhein-Westfalen', 'Rheinland-Pfalz',
                    'Saarland', 'Sachsen', 'Sachsen-Anhalt',
                    'Schleswig-Holstein', 'Thüringen']
SOURCES_LIST = ['Erdgas', 'Braunkohle', "Steinkohle", "Kernenergie", OIL]
OPSTATES = ['in Betrieb', 'Gesetzlich an Stilllegung gehindert',
            'Sicherheitsbereitschaft', 'Netzreserve', 'Sonderfall',
            'vorläufig stillgelegt', 'stillgelegt']
ACTIVE_OPS = OPSTATES[0:3]
DEFAULT_OPSTATES = ['in Betrieb', 'Gesetzlich an Stilllegung gehindert',
                    'Sicherheitsbereitschaft', 'Netzreserve', 'Sonderfall']
DEFAULT_OPS = DEFAULT_OPSTATES
SELECT_CHP = [("Nein", "keine Kraft-Wärme-Kopplung"),
                ("Ja", "Kraft-Wärme-Kopplung"), ("", "unbekannt")]
SELECT_CHP_LIST = ["Ja", "Nein", ""]
SOURCES_DICT = {'Erdgas': 1220, 'Braunkohle': 6625, "Steinkohle": 3000,
                    "Kernenergie": 6700, OIL: 1000}
FULL_YEAR = 8760

PLANT_COLOR_MAPPING = {"Steinkohle": "table-danger", "Braunkohle": "table-warning",
                        "Erdgas": "table-success", "Kernenergie": "table-info",
                        OIL: "table-secondary"}
HEADER_BLOCKS = ['Kraftwerk','Block', 'Krafwerksname', 'Blockname',
                    'Inbetriebnahme', 'Abschaltung', 'KWK', 'Status',
                    'Bundesland', 'Nennleistung [in MW]']
SOURCES_PLANTS = [ENERGY_SOURCE, "Anzahl", NETOP, YEARLY_PRD, "CO2 [Mio. t]",
                    "Volllaststunden [h]", "Auslastung [%]", "Effizienz [g CO2/kWh]"]
SOURCES_BLOCKS = [ENERGY_SOURCE, "Anzahl", NETOP, YEARLY_PRD, "Volllaststunden [h]",
                    "Auslastung 2018 [%]", "Auslastung 2019 [%]"]


SOURCES_BLOCKS_OLD = [ENERGY_SOURCE, "Anzahl", NETOP, YEARLY_PRD,
                        "Volllaststunden [" + str(YEAR) + "]",
                        "Auslastung [" + str(YEAR) + "] [%]",
                        "Auslastung [" + str(LATEST_YEAR) + "] [%]"]


API_KEY = "AIzaSyAWz7ee-a1eLUZ9aGJTauKxAMP1whRKlcE"