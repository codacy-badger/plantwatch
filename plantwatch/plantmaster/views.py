#!/usr/bin/env python
# -*- coding: utf-8 -*-


from .forms import BlocksForm
from .models import Blocks, Plants, Power, Addresses, Month, Pollutions, Monthp, Mtp, Yearly

from django.db.models import Sum, Min, Avg, Max, Count
from django.db.models import Q, F, When, Case, FloatField
from django.db.models import OuterRef, Subquery
from django.forms.models import model_to_dict
from django.shortcuts import render, get_object_or_404, redirect

from functools import reduce
from datetime import date, datetime
import calendar
import json
import random

HOURS_IN_YEAR = 365 * 24
PRTR_YEARS = list(range(2007, 2019))
ENERGY_YEARS = list(range(2015, 2020))
YEARS = ENERGY_YEARS
YEAR = PRTR_YEARS[-1]
LATEST_YEAR = ENERGY_YEARS[-1]

FULL_HOURS = "Volllaststunden [" + str(YEAR) + "]"

FEDERAL_STATES = ['Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen', 'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen', 'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen', 'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen']
SOURCES_LIST = ['Erdgas', 'Braunkohle', "Steinkohle", "Kernenergie", "Mineralölprodukte"]
SORT_CRITERIA_BLOCKS = ([('blockname', 'Name'), ('netpower', 'Nennleistung'), ('initialop', 'Inbetriebnahme')], "netpower")
SORT_CRITERIA_PLANTS = ([('plantname', 'Name'), ('totalpower', 'Gesamtleistung'),('initialop', 'Inbetriebnahme'), ('latestexpanded', 'Zuletzt erweitert'), ('eff', 'Effizienz'), ('workload', 'Auslastung'), ('co2', 'CO2 Ausstoß'), ('energy', 'Energie')], "totalpower")
SORT_CRITERIA_PLANTS_OLD = ([('plantname', 'Name'), ('totalpower', 'Gesamtleistung'),('initialop', 'Inbetriebnahme'), ('latestexpanded', 'Zuletzt erweitert')], "totalpower")
OPSTATES = ['in Betrieb', 'Gesetzlich an Stilllegung gehindert', 'Sicherheitsbereitschaft', 'Netzreserve', 'Sonderfall', 'vorläufig stillgelegt', 'stillgelegt']
ACTIVE_OPS = OPSTATES[0:3]
DEFAULT_OPSTATES = OPSTATES[0:5]
SELECT_CHP = [("Nein", "keine Kraft-Wärme-Kopplung"), ("Ja", "Kraft-Wärme-Kopplung"), ("", "unbekannt")]
SELECT_CHP_LIST = ["Ja", "Nein", ""]
SOURCES_DICT = {'Erdgas': 1220, 'Braunkohle': 6625, "Steinkohle": 3000, "Kernenergie": 6700, "Mineralölprodukte": 1000}
FULL_YEAR = 8760
SLIDER_1 = "1950;2025"
SLIDER_2p = "300;4500"
SLIDER_2b = "250;1500"
PLANT_COLOR_MAPPING = {"Steinkohle": "table-danger", "Braunkohle": "table-warning", "Erdgas": "table-success", "Kernenergie": "table-info", "Mineralölprodukte": "table-secondary"}
HEADER_BLOCKS = ['Kraftwerk','Block', 'Krafwerksname', 'Blockname', 'Inbetriebnahme', 'Abschaltung', 'KWK', 'Status', 'Bundesland', 'Nennleistung [in MW]']
SOURCES_BLOCKS = ["Energieträger [" + str(YEAR) + "]", "Anzahl", "Nennleistung [GW]", "Jahresproduktion [TWh]", "Volllaststunden [h]", "Auslastung [%]", "Effizienz [g CO2/kWh]"]
SOURCES_BLOCKS_OLD = ["Energieträger", "Anzahl", "Nennleistung [GW]", "Jahresproduktion [TWh]", "Volllaststunden [" + str(YEAR) + "]", "Auslastung [" + str(YEAR) + "] [%]", "Auslastung [" + str(LATEST_YEAR) + "] [%]"]


API_KEY = "AIzaSyAWz7ee-a1eLUZ9aGJTauKxAMP1whRKlcE"




SL_1 = [1950, 2025, 1950, 2025, 5]
SL_2b = [250, 1500, 0, 1500, 250]
SL_2p = [250, 4500, 0, 4500, 250]


def filter_and(queryset, filtered, filters):
    for afilter in filters:
        queryset = filter_queryset(queryset, filtered, afilter)
    return queryset


def filter_or(queryset, filtered, filters):
    """Chain or filters
    Thanks to https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django"""
    query = reduce(lambda q, value: q | Q(**{filtered: value}), filters, Q())
    queryset = queryset.all().filter(query)
    return queryset


def filter_queryset(queryset, filtered, afilter):
    param = {filtered: afilter}
    new_queryset = queryset.all().filter(**param)
    return new_queryset


def forge_sources_dict(block_list, power_type):

    sources_dict = {}
    whole_power, whole_power2 = 0, 0
    factors = []
    for source in SOURCES_LIST:
        tmp = filter_or(block_list, "energysource", [source])
        count = tmp.all().count()
        raw_power = tmp.all().aggregate(Sum(power_type))[power_type + '__sum'] or 0
        raw_energy = Month.objects.filter(blockid__in=tmp, year=YEAR, month__in=list(range(1,13))).aggregate(Sum("power"))['power__sum'] or 0
        energy = raw_energy / 10**6

        factor = divide_safe(raw_energy, raw_power)

        raw_energy2 = Month.objects.filter(blockid__in=tmp, year=LATEST_YEAR, month__in=list(range(1,13))).aggregate(Sum("power"))['power__sum'] or 0
        energy2 = raw_energy2 / 10**6
        workload = calc_workload(raw_energy * 10000, raw_power)
        workload2 = calc_workload(raw_energy2 * 10000, raw_power)
        factors.append(factor)
        power = round(raw_power / 1000, 2)
        anual_power = round((raw_power * factor) / (10**6), 2)
        whole_power += energy
        whole_power2 += energy2

        sources_dict[source] = [count, power, round(energy, 2), round(factor, 2), round(workload, 2), round(workload2, 2)]
    power_c = block_list.all().aggregate(Sum(power_type))[power_type + '__sum'] or 1
    power = round(power_c / 1000, 2)
    count = block_list.all().count()
    sources_dict["Summe"] = [count, power, round(whole_power, 2), round(divide_safe(whole_power * 10000, raw_power), 2), round(calc_workload(whole_power * 10**10, power_c), 2), round(calc_workload(whole_power2 * 10**10, power_c), 2)]
    return sources_dict

def force_sources_plant(annotated_plants):

    sources_dict = {}
    energy, energy2 = 0, 0

    total_power = 0
    total_energy = 0
    total_co2 = 0
    total_count = 0

    for source in SOURCES_LIST:
        # TODO: introduce effective power besides totalpower
        # TODO: show in plant active and inactive plants, separately
        filtered = annotated_plants.filter(energysource=source)
        count = filtered.count()
        effective_power = filtered.aggregate(Sum('totalpower'))['totalpower__sum'] or 0
        energy = filtered.aggregate(Sum('energy_2018'))['energy_2018__sum'] or 0
        co2 = filtered.aggregate(Sum('co2_2018'))['co2_2018__sum'] or 0
        workload = calc_workload(energy, effective_power)
        ophours = divide_safe(energy, effective_power)
        efficiency = divide_safe(co2, energy)

        total_power += effective_power
        total_energy += energy
        total_co2 += co2
        total_count += count
    
        sources_dict[source] = [count, effective_power / 1000, energy / 10**6, ophours, workload * 10000, efficiency]
    
    sources_dict['Summe'] = [total_count, total_power / 1000, total_energy / 10**6, divide_safe(total_energy, total_power), calc_workload(total_energy, total_power) * 10000, divide_safe(total_co2, total_energy)]
    return sources_dict


def handle_sliders(sliders):
    new_sliders = list(map(handle_slider, sliders))
    return new_sliders


def handle_slider(slider):
    new_slider = list(map(int, slider.split(';')))
    return new_slider


def handle_slider_1(slider):
    new_slider = handle_slider(slider)
    new_slider.extend(SL_1[2:])
    return new_slider


def handle_slider_2(slider, is_plants):
    new_slider = handle_slider(slider)
    if is_plants:
        new_slider.extend(SL_2p[2:])
    else:
        new_slider.extend(SL_2b[2:])
    # raise TypeError(new_slider)
    return new_slider


def initialize_form(request, SORT_CRITERIA=SORT_CRITERIA_BLOCKS, plants=False):
    slider1 = SLIDER_1

    if plants:
        sl2 = SLIDER_2p
    else:
        sl2 = SLIDER_2b
    slider2 = sl2
    sort_criteria = SORT_CRITERIA[1]
    sort_method = "-"
    search_federalstate = []
    search_power = ['Braunkohle', "Steinkohle", "Kernenergie", "Mineralölprodukte", "Erdgas"]
    search_opstate = DEFAULT_OPSTATES
    search_chp = []

    if request.method == 'POST':
        form = BlocksForm(request.POST)
        sort_criteria = request.POST.get('sort_by', SORT_CRITERIA[1])
        search_federalstate = request.POST.getlist('select_federalstate', [])
        search_power = request.POST.getlist('select_powersource', [])
        search_opstate = request.POST.getlist('select_opstate', DEFAULT_OPSTATES)
        search_chp = request.POST.getlist('select_chp', [])
        slider1 = request.POST.get('slider1', SLIDER_1)
        slider2 = request.POST.get('slider2', sl2)
        sort_method = request.POST.get('sort_method', sort_method)
    else:
        form = BlocksForm()

    form.fields['sort_by'].choices = SORT_CRITERIA[0]
    form.fields['sort_by'].initial = sort_criteria or SORT_CRITERIA[1]
    form.fields['sort_by'].label = "Sortiere nach:"

    form.fields['sort_method'].choices = [('-', 'absteigend'), ('', 'aufsteigend')]
    form.fields['sort_method'].initial = sort_method
    form.fields['sort_method'].label = "aufsteigend oder absteigend?"

    form.fields['select_chp'].choices = SELECT_CHP
    form.fields['select_chp'].initial = search_chp or SELECT_CHP_LIST
    form.fields['select_chp'].label = "Filtere nach Kraft-Wärme-Kopplung:"

    form.fields['select_federalstate'].choices = list(zip(FEDERAL_STATES, FEDERAL_STATES))
    form.fields['select_federalstate'].initial = search_federalstate  # or FEDERAL_STATES
    form.fields['select_federalstate'].label = "Filtere nach Bundesland:"

    form.fields['select_powersource'].choices = list(zip(SOURCES_LIST, SOURCES_LIST))
    form.fields['select_powersource'].initial = search_power or SOURCES_LIST
    form.fields['select_powersource'].label = "Filtere nach Energieträger:"

    form.fields['select_opstate'].choices = list(zip(OPSTATES, OPSTATES))
    form.fields['select_opstate'].initial = search_opstate or ['in Betrieb', 'Gesetzlich an Stilllegung gehindert',
                                                               'Netzreserve', 'Sicherheitsbereitschaft', 'Sonderfall']
    form.fields['select_opstate'].label = "Filtere nach Betriebszustand:"

    form.fields['slider1'].initial = slider1
    form.fields['slider1'].label = "Filtere nach Zeitraum"

    form.fields['slider2'].initial = slider2
    form.fields['slider2'].label = "Filtere nach Nennleistung"

    if not search_power:
        search_power = SOURCES_LIST
    if not search_opstate:
        search_opstate = ["in Betrieb", "Sonderfall", "Gesetzlich an Stilllegung gehindert"]
    if not search_chp:
        search_chp = ["Nein", "Ja", ""]
    if not search_federalstate:
        search_federalstate = FEDERAL_STATES

    slider_1 = handle_slider_1(slider1)
    slider_2 = handle_slider_2(slider2, plants)
    # raise TypeError(slider_2)
    return form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, [slider_1,
                                                                                                             slider_2]


def create_block_list(block_list, filter_dict):
    for filter_tag, filtered in filter_dict.items():
        block_list = filter_or(block_list, filter_tag, filtered)
    return block_list


def efficiency(request):
    form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, sliders = initialize_form(
        request)

    #  lower, upper = create_low_up(slider1)

    block_list = Blocks.objects.order_by(sort_method + sort_criteria)
    filter_dict = {"energysource": search_power, "state": search_opstate, "federalstate": search_federalstate,
                   "chp": search_chp}
    block_list = create_block_list(block_list, filter_dict)

    block_list = block_list.filter(initialop__range=sliders[0][0:1])
    block_list = block_list.filter(fullload__is_null=False)
    block_list = block_list.filter(pollutions__pollutant="CO2")
    block_list = block_list.filter(pollutions__pollutant="CO2")
    block_list = block_list.annotate(fullload=(F('blocks__netpower') * F('monthly') * FULL_YEAR))
    block_list = block_list.annotate(efficiency=(F('')))

    sources_dict = forge_sources_dict(block_list, "netpower")

    block_list = block_list[::1]
    block_tmp_dict = list(map(model_to_dict, block_list))
    value_list = ["blockname", "initialop", "endop", "chp", "state", "federalstate", "fullload", "netpower"]
    key_list = ["energysource", "blockid", "plantid"]
    block_dict = create_blocks_dict(block_tmp_dict, value_list, key_list)

    header_list = ['Kraftwerk', 'Block', 'Name', 'Inbetriebnahme', 'Abschaltung', 'KWK', 'Status', 'Bundesland',
                   'Volllast [in %]', 'Nennleistung [in MW]']
    sources_header = ["Energieträger", "Anzahl", "Nennleistung [in MW]", "Jahresproduktion [in TWh]",
                      "Volllaststunden [pro Jahr]"]
    context = {
        'header_list': header_list,
        'form': form,
        'block_dict': block_dict,
        'sources_dict': sources_dict,
        'sources_header': sources_header,
        'plant_mapper': PLANT_COLOR_MAPPING,
        'range': range(2),
    }
    return render(request, 'plantmaster/blocks.html', context)


def blocks(request):
    form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, sliders = initialize_form(request)
    # slider = list(map(create_low_up, sliders))
    slider = sliders

    block_list = Blocks.objects.order_by(sort_method + sort_criteria)
    filter_dict = {"energysource": search_power, "state": search_opstate, "federalstate": search_federalstate, "chp": search_chp}
    block_list = create_block_list(block_list, filter_dict)

    # print(block_list)

    block_list = block_list.filter(initialop__range=(slider[0][0], slider[0][1]))
    block_list = block_list.filter(netpower__range=(slider[1][0], slider[1][1]))

    # print(block_list)

    sources_dict = forge_sources_dict(block_list, "netpower")

    block_list = block_list[::1]
    block_tmp_dict = list(map(model_to_dict, block_list))
    value_list = ["blockname", "blockdescription", "initialop", "endop", "chp", "state", "federalstate", "netpower"]
    key_list = ["energysource", "blockid", "plantid"]
    block_dict = create_blocks_dict(block_tmp_dict, value_list, key_list)

    header_list = HEADER_BLOCKS
    sources_header = SOURCES_BLOCKS
    context = {
        'header_list': header_list,
        'slider': slider,
        'form': form,
        'block_dict': block_dict,
        'sources_dict': sources_dict,
        'sources_header': sources_header,
        'plant_mapper': PLANT_COLOR_MAPPING,
        'range': range(2),
    }
    return render(request, 'plantmaster/blocks.html', context)


def create_blocks_dict(block_tmp_dict, value_list, key_list):
    block_dict = {}
    # print(key_list)
    for entry in block_tmp_dict:
        key = []
        for a_key in key_list:
            key.append(entry[a_key])
        value = []
        for element in value_list:
            value.append(entry[element])
            block_dict[tuple(key)] = value
    return block_dict


def impressum(request):
    return render(request, "plantmaster/impressum.html", {})

def divide_safe(n, d):
    return n / d if d else 0

def calc_workload(energy, power):
    return divide_safe(energy, (power * HOURS_IN_YEAR) * 100)

def calc_efficency(co2, energy):
    return divide_safe(co2, energy) * 10**3

def plants3(request):
    form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, slider = initialize_form(request, SORT_CRITERIA=SORT_CRITERIA_PLANTS, plants=True)
    plant_list = Plants.objects.filter(initialop__range=(slider[0][0], slider[0][1])).filter(totalpower__range=(slider[1][0], slider[1][1])).annotate(block_count=Count('blocks__plantid')).order_by(sort_method + sort_criteria)

    t = plant_list.first()

    bc = t.block_count
    return render(request, 'plantmaster/blocks.html', context)


def plants_old(request):
    start = datetime.now()
    form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, slider = initialize_form(request, SORT_CRITERIA=SORT_CRITERIA_PLANTS_OLD, plants=True)
    plant_list = Plants.objects.filter(initialop__range=(slider[0][0], slider[0][1])).filter(totalpower__range=(slider[1][0], slider[1][1])).filter(federalstate__in=search_federalstate).filter(state__in=search_opstate).filter(chp__in=search_chp).order_by(sort_method + sort_criteria)

    p, q, z = 1, 2, 3

    q = [1, 2, 3]

    q = plant_list

    filter_dict = {"energysource": search_power, "state": search_opstate, "federalstate": search_federalstate}
    block_list = Blocks.objects.filter(plantid__in=plant_list.values("plantid"))
    # block_list = block_list.filter(initialop__range=(slider[0][0], slider[0][1]))
    # block_list = block_list.filter(netpower__range=(slider[1][0], slider[1][1]))
    block_list = create_block_list(block_list, filter_dict)
    plant_list = create_block_list(plant_list, filter_dict)

    sources_dict = forge_sources_dict(block_list, "netpower")

    #plant_list = plant_list[::1]
    plant_tmp_dict = list(map(model_to_dict, plant_list))
    plant_tmp_list = []

    for plant_dict_entry in plant_tmp_dict:
        plant_list_entry = plant_dict_entry
        plantid = plant_dict_entry["plantid"]
        blocks_list = Blocks.objects.all().filter(plantid=plantid)
        initialop = blocks_list.all().aggregate(Min('initialop'))['initialop__min']
        plant_list_entry["initialop"] = initialop
        energy = get_energy_for_plant(plantid, YEAR)
        co2 = get_co2_for_plant_by_year(plantid, YEAR)
        tpl =  plant_list_entry["totalpower"]
        plant_list_entry["co2"] = co2
        plant_list_entry["energy"] = round(energy, 2)
        plant_list_entry["workload"] = round(calc_workload(get_energy_for_plant(plantid, ENERGY_YEARS[-1], raw=True) * 10000, tpl), 2)
        plant_list_entry["efficency"] = int(calc_efficency(co2, energy))
        plant_list_entry["totalpower"] = round(plant_list_entry["totalpower"], 1)
        plant_tmp_list.append(plant_list_entry)

    value_list = ["plantname", "initialop", "latestexpanded", "state", "federalstate", "totalpower", "energy", "workload", "efficency"]
    key_list = ["energysource", "plantid", "plantid"]
    block_dict = create_blocks_dict(plant_tmp_dict, value_list, key_list)

    header_list = ['Kraftwerk', 'Name', 'Inbetrieb-nahme', 'zuletzt erweitert', 'Status', 'Bundesland', 'Gesamt-leistung [MW]', 'Energie [TWh]', 'Auslastung [%]', 'Effizienz [g/kWh]']
    sources_header = SOURCES_BLOCKS_OLD
    slider_list = slider

    end = datetime.now()
    diff = end - start
    res = [start, end, diff]
    res = []
    context = {
        'header_list': header_list,
        'slider': slider_list,
        'form': form,
        'plant_mapper': PLANT_COLOR_MAPPING,
        'block_dict': block_dict,
        'sources_dict': sources_dict,
        'sources_header': sources_header,
        'range': range(2),
        'q': q,
        'p': p,
        'z': z,
        'res': res,
    }
    return render(request, 'plantmaster/blocks.html', context)


def plants(request):
    start = datetime.now()
    form, search_power, search_opstate, search_federalstate, search_chp, sort_method, sort_criteria, slider = initialize_form(request, SORT_CRITERIA=SORT_CRITERIA_PLANTS, plants=True)
    tmp = Plants.objects.filter(initialop__range=(slider[0][0], slider[0][1])).filter(totalpower__range=(slider[1][0], slider[1][1])).filter(federalstate__in=search_federalstate).filter(state__in=search_opstate).filter(chp__in=search_chp).order_by(sort_method + sort_criteria)
    plc = tmp.count()

    power_type = "totalpower"
    power_type = "activepower"
    
    tmp3 = tmp.all().annotate(
    eff15=Case(
        When(energy_2015=0, then=0),
        When(co2_2015=0, then=0),
        default=(F('co2_2015') / F('energy_2015')), output_field=FloatField()),
    eff16=Case(
        When(energy_2016=0, then=0),
        When(co2_2016=0, then=0),
        default=(F('co2_2016') / F('energy_2016')), output_field=FloatField()),
    eff17=Case(
        When(energy_2017=0, then=0),
        When(co2_2017=0, then=0),
        default=(F('co2_2017') / F('energy_2017')), output_field=FloatField()),
    eff18=Case(
        When(energy_2018=0, then=0),
        When(co2_2018=0, then=0),
        default=(F('co2_2018') / F('energy_2018')), output_field=FloatField()),
    eff=Case(
        When(energy_2018=0, then=0),
        When(co2_2018=0, then=0),
        default=(F('co2_2018') / F('energy_2018')), output_field=FloatField()),
    workload15=Case(
        When(energy_2015=0, then=0),
        default=(F('energy_2015') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    workload16=Case(
        When(energy_2016=0, then=0),
        default=(F('energy_2016') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    workload17=Case(
        When(energy_2017=0, then=0),
        default=(F('energy_2017') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    workload18=Case(
        When(energy_2018=0, then=0),
        default=(F('energy_2018') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    workload19=Case(
        When(energy_2019=0, then=0),
        default=(F('energy_2019') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    workload=Case(
        When(energy_2019=0, then=0),
        default=(F('energy_2019') / (F(power_type) * HOURS_IN_YEAR) * 100), output_field=FloatField()),
    energy=Case(
        When(energy_2018=0, then=0),
        default=(F('energy_2018') / float(10**6)), output_field=FloatField()),
    co2=Case(
        When(co2_2018=0, then=0),
        default=(F('co2_2018') / float(10**9)), output_field=FloatField()),
    )

    plant_list = tmp3.order_by(sort_method + sort_criteria)

    p, q, z = 1, 2, 3
    q = [1, 2, 3]

    filter_dict = {"energysource": search_power, "state": search_opstate, "federalstate": search_federalstate}
    sources_dict = force_sources_plant(plant_list)

    block_list = []
    block_dict = {}

    value_list = ["plantname", "initialop", "latestexpanded", "state", "federalstate", "totalpower", "energy", "workload", "efficency"]
    key_list = ["energysource", "plantid", "plantid"]

    header_list = ['Kraftwerk', 'Name', 'Unternehmen', 'Inbetrieb-nahme', 'zuletzt erweitert', 'Status', 'Bundesland', 'Gesamt-leistung [MW]', 'Energie [TWh]', 'CO2 Ausstoß [Mio. t]', 'Auslastung [%]', 'Effizienz [g/kWh]']
    sources_header = SOURCES_BLOCKS
    slider_list = slider

    end = datetime.now()
    diff = end - start
    res = [start, end, diff]

    res = []
    context = {
        'header_list': header_list,
        'slider': slider_list,
        'form': form,
        'plant_mapper': PLANT_COLOR_MAPPING,
        'block_dict': {},
        'sources_dict': sources_dict,
        'sources_header': sources_header,
        'plant_list': plant_list,
        'range': range(2),
        'q': q,
        'p': p,
        'z': z,
        'res': res,
    }
    return render(request, 'plantmaster/plants.html', context)

def query_for_month_many2(blocks, year, month):
    start_date = date(year, month, 1)
    end_date = date(year, month+1, 1)
    q = Power.objects.filter(blockid__in=blocks)
    power = q.filter(producedat__range=(start_date, end_date)).aggregate(Sum("power"))['power__sum']
    return power or 0


def query_for_month_many(blocks, year, month):
    q = Month.objects.filter(blockid__in=blocks)
    power = q.filter(year=year, month=month).aggregate(Sum("power"))['power__sum']
    return power or 0

def query_for_month(blockid, year, month):
    q = Month.objects.filter(blockid=blockid)
    power = q.filter(year=year, month=month).aggregate(Sum("power"))['power__sum']
    return power or 0

def query_for_year_all(blocks, year):
    q = Month.objects.filter(blockid__in=blocks)
    power = q.filter(year=year).aggregate(Sum("power"))['power__sum']
    return power or 0

def query_for_year(blockid, year):
    q = Month.objects.filter(blockid=blockid)
    power = q.filter(year=year).aggregate(Sum("power"))['power__sum']
    return power or 0

def query2(block):
    power = Power.objects.filter(blockid=block.blockid, producedat__date=date(2018, 8, 13))
    return power

def query(block):
    q = Power.objects.filter(blockid=block.blockid)
    return q

def get_aggs(q):
    minimum = q.aggregate(Min("power"))['power__min']
    maximum = q.aggregate(Max("power"))['power__max']
    avg = q.aggregate(Avg("power"))['power__avg']
    return ["power", minimum, maximum, avg]

def get_for_year(q, year):
    power = q.filter(producedat__year=year)

    return power


def block(request, blockid):
    block = get_object_or_404(Blocks, blockid=blockid)

    address = get_object_or_404(Addresses, blockid=blockid)
    plant_id = block.plantid.plantid
    error = True if not plant_id else False

    data_list = [plant_id, block.blockid, block.blockname, block.blockdescription, block.company, address.plz, address.place, address.street, address.federalstate, block.netpower]
    header_list = ['PlantID', 'BlockID', 'Plantname', 'Blockname', 'Unternehmen', 'PLZ', 'Ort', 'Anschrift', 'Bundesland', 'Nennleistung']
    context = {
        'data_list': zip(header_list, data_list),
        'plant_id': plant_id,
        'error': error
    }
    return render(request, "plantmaster/block.html", context)


#def plant(request, plantid):
#    return plant_year(request, plantid, 2019)

def gen_row_m(blocknames, year):
    m1 = list(range(1,13))
    return list(map(lambda x: query_for_month_many(blocknames, year, x), m1))

def gen_row_y(blocknames, year):
    return list(map(lambda x: query_for_year(x, year), blocknames))

def get_chart_data_m(blocknames, years):


    m1 = list(range(1,13))
    
    #head = get_month_header()

    powers = []
    for i in years:
        p = [i] + gen_row_m(blocknames, i)
        powers.append(p)
    
    #print(powers)
    return powers

def get_month_header():
    m1 = list(range(1,13))

    m2 = ['x'] + list(map(lambda x: calendar.month_abbr[x], m1))
    return m2

def get_chart_data_b(blocknames, year):

    powers = []
    for block in blocknames:
        p = [block.blockid] + gen_row_m([block], year)
        powers.append(p)
    
    #print(powers)
    return powers

def get_chart_data_whole_y2(blocknames, year):

    #head = ["x"] + blocknames
    powers = []
    for block in blocknames:
        p = [block.blockid] + gen_row_y([block], year)
        powers.append(p)
    
    #print(powers)
    return powers

def get_chart_data_whole_y(blocknames, years):
    head = ["x"] + years
    powers = [head]
    for block in blocknames:
        p = [block.blockid] + [gen_row_y([block], year) for year in years]
        powers.append(p)
    
    #print(powers)
    return powers

def get_chart_data_y(blocknames, years):

    #head = ["x"] + blocknames
    powers = []
    for i in years:
        p = [i] + gen_row_y(blocknames, i)
        powers.append(p)
    
    #print(powers)
    return powers

def get_block_power(blockid):
    block = Blocks.objects.get(blockid=blockid)
    netpower = block.netpower
    return

def get_gague_from_powers(powers):

    years = powers[0][1:]
    data = powers[1:]
    
    blocks = [x[0] for x in data]
    vals = [x[1:] for x in data]

    block_power = [get_block_power(block) for block in blocks]

    percentage = [HOURS_IN_YEAR for idx, p in enumerate(block_power)]
    percentage = [HOURS_IN_YEAR for p in block_power]

def get_percentages_from_yearprod3(plant):

    energies = [get_energy_for_plant(plant, x, raw=True) for x in YEARS]
    workloads = [divide_safe(e, (plant.totalpower * HOURS_IN_YEAR)) * 100 for e in energies]

    workloads.insert(0, plant.plantid)
    result = [workloads]

    head = ['x'] + YEARS
    result.insert(0, head)

    return result

def get_percentages_from_yearprod2(yearprod, blocks):

    data = yearprod[1:]
    blocks_str = [x[0] for x in data]
    vals = [x[1:] for x in data]

    block_power = [block.netpower for block in blocks]
    percentage = [[[value[0] * 100 / (HOURS_IN_YEAR * block_power[idx])] for value in entry] for idx, entry in enumerate(vals)]
    blocks_percs = [[[blocks_str[idx]] + entry] for idx, entry in enumerate(percentage)]

    #p4 = [x[0] for x in blocks_percs]
    result = [x[0] for x in blocks_percs]
    blocks_str.insert(0, 'x')

    head = yearprod[0]
    result.insert(0, head)

    return result

def get_energy_for_plant(plantid, year, raw=False):
    try:
        tmp = Monthp.objects.filter(plantid=plantid, year=year).aggregate(Sum('power'))['power__sum'] or 0
    except:
        tmp = 0.001

    if raw:
        return tmp
    else:
        return tmp / 10**6 or 0

def get_co2_for_plant_by_year(plantid, year):
    try:
        co2 = Pollutions.objects.get(plantid=plantid, releasesto="Air", pollutant="CO2", year=year).amount2
    except:
        co2 = 0
    return co2# or 1

def get_company(company):

    tmp = company.replace("Kraftwerk", "").strip()
    tmp = tmp.replace("Stadtwerke", "").strip()

    cl = tmp.split(" ")
    l = len(cl)
    if l == 1:
        return company
    elif l > 1:
        return "" if "niper" in company else "RWE Power" if "RWE" in company else cl[0] if "ENGIE" in company else cl[0]
    else:
        return ""

def get_plantname(plantname):
    tmp = plantname.replace("Kraftwerk", "").strip()
    tmp = plantname.replace("HKW", "").strip()
    l = len(tmp)

    if l < 4:
        return tmp if "GKM" in tmp else ""
    else:
        return tmp

def random_plant(request):
    i = Plants.objects.filter(state__in=DEFAULT_OPSTATES).filter(totalpower__gte=300).filter(Q(energysource="Steinkohle") | Q(energysource="Braunkohle")).all()
    #j = i.filter(totalpower__range(300,5000))
    #items = list(map(lambda x: x.plantid, i))
    l = len(i)

    # change 3 to how many random it/06-05-300-0326774/ems you want
    random_item = i[random.randint(0, l - 1)] #random.sample(i, 1)
    # if you want only a single random item
    return redirect('plant', random_item.plantid)
    

def get_co2(plantid):
    for year in PRTR_YEARS[::-1]:
        try:
            q = Pollutions.objects.get(plantid=plantid, year=year, releasesto='Air', pollutant="CO2")
            break
        except:
            pass
    return q

def get_pollutants(plantid, year=''):
    #TODO: fix to display least recent pollutant year instead of fixed year
    if year:
        return Pollutions.objects.filter(plantid=plantid, year=year, releasesto='Air').order_by("-exponent", "-amount")

    for year in PRTR_YEARS[::-1]:
        q = Pollutions.objects.filter(plantid=plantid, year=year, releasesto='Air').order_by("-exponent", "-amount")
        if q.exists():
            return year, q

def get_pollutants_any_year(plantid):
    q = Pollutions.objects.filter(plantid=plantid, releasesto='Air').order_by("-exponent", "pollutant2", "year", "-amount")
    return q

def get_pollutant_dict(plantid, blocks):
    try:
        year, pollutions = get_pollutants(plantid)
    except TypeError:
        return {}
    co2 = get_co2_for_plant_by_year(plantid, year)
    energy = get_energy_for_plant(plantid, year)
    pollutants_tmp_dict = list(map(model_to_dict, pollutions))
    pol_list = ["year", "amount2", "unit2"]
    pk_list = ["year", "pollutant", "amount2"]
    pollutants_dict = create_blocks_dict(pollutants_tmp_dict, pol_list, pk_list)
    return pollutants_dict

def get_activepower(blocks):
    powers = []

    for x in YEARS:
        activeblocks = blocks.filter(Q(state__in=ACTIVE_OPS[0:1]) | (Q(state=ACTIVE_OPS[2]) & Q(reserveyear__gt=x) | ((Q(state="stillgelegt") & Q(endop__gt=x)))))
        activepower = activeblocks.aggregate(Sum('netpower'))['netpower__sum'] # or 0
        powers.append(activepower)

    return powers


def get_elist(plantid, plant):

    elist = []

    blocks = Blocks.objects.filter(plantid=plantid)

    powers = get_activepower(blocks)

    energies = [get_energy_for_plant(plantid, x) for x in YEARS]
    e2s = [get_energy_for_plant(plantid, x, raw=True) for x in YEARS]
    co2s = [get_co2_for_plant_by_year(plantid, x) for x in YEARS]
    tmp = list(zip(co2s, energies))
    effs = [divide_safe(x, y) * 10**3 for x, y in tmp]
    workload2 = [divide_safe(e, (plant.totalpower * HOURS_IN_YEAR)) * 100 for e in e2s]
    workload = [divide_safe(e, (p * HOURS_IN_YEAR)) * 100 for (e, p) in zip(e2s, powers)]

    effcols = list(zip(YEARS, energies, co2s, effs, workload, workload2))
    testval = reduce(lambda a, b: a + b, [i for col in effcols for i in col[1:]])

        # all rows empty, so return emptylist
    if testval == 0:
        return elist
    else:
        return [["Jahr", "Energie TWh", "CO2 [Mio. t.]", "g/kWh", "Auslastung aktive Blöcke [%]", "Auslastung gesamt [%]"], effcols]

def plant(request, plantid):

    plant = get_object_or_404(Plants, plantid=plantid)
    blocks = Blocks.objects.filter(plantid=plantid)

    monthp = Monthp.objects.filter(plantid=plantid, year=YEAR).aggregate(Sum('power'))
    energies = [get_energy_for_plant(plantid, x) for x in PRTR_YEARS]


    pltn, comp = get_plantname(plant.plantname), get_company(plant.company)
    ks = " Kraftwerk " if "raftwerk" not in pltn else pltn
    ss3 = comp + ks + pltn
    ss3 = plant.plantname.replace("Werk", "") if "P&L" in plant.plantname else ss3
    ss3 = ss3.replace(" ", "+")
    ss3 = ss3.replace("&", "%26")
    #ss3 = ss3.replace("/", "&#x2F")

    pollutants_dict = get_pollutant_dict(plantid, blocks)

    pol_list = ["year", "amount2", "unit2"]
    pk_list = ["year", "pollutant", "amount2"]
    pol_header_list = ['Schadstoff', 'Jahr', 'Wert', 'Einheit']

    elist = get_elist(plantid, plant)

    blocks_list = blocks.order_by("initialop" + "")
    plantname = plant.plantname
    block_count = plant.blockcount
    le = plant.latestexpanded
    tp = plant.totalpower    

    blocks_tmp_dict = list(map(model_to_dict, blocks_list))
    value_list = ["blockname", "blockdescription", "initialop", "endop", "chp", "state", "federalstate", "netpower"]
    key_list = ["energysource", "blockid", "plantid"]
    blocks_of_plant = create_blocks_dict(blocks_tmp_dict, value_list, key_list)

    blocks_header_list = ['BlockID', 'Kraftwerksname', 'Blockname', 'Inbetriebnahme', 'Abschaltung', 'KWK', 'Status', 'Bundesland', 'Nennleistung [in MW]']
    data_list = [plantid, plantname, plant.company, block_count, le, tp, plant.activepower]
    header_list = ['KraftwerkID', 'Kraftwerkname', 'Unternehmen', 'Blockzahl', 'zuletzt erweitert', 'Gesamtleistung', 'Aktive Leistung']

    pollutions2 = get_pollutants_any_year(plantid)

    context = {
        'data_list': zip(header_list, data_list),
        'header_list': blocks_header_list,
        'blocks_of_plant': blocks_of_plant,
        'pollutants_dict': pollutants_dict,
        'pol_header_list': pol_header_list,
        'plant_id': plantid,
        'ss': ss3,
        'elist': elist,
        'energies': energies,
        'API': API_KEY,
        'pollutions2': pollutions2,
    }
    return render(request, "plantmaster/plant.html", context)


def plant2(request, plantid):

    plant = get_object_or_404(Plants, plantid=plantid)
    blocks = Blocks.objects.filter(plantid=plantid).order_by("initialop" + "")
    blocks_list = blocks #blocks.order_by("initialop" + "")
    plantname = plant.plantname
    block_count = plant.blockcount
    le = plant.latestexpanded
    tp = plant.totalpower

    power, minp, maxp, avg = 0, 0, 0, 0
    powers = [minp, maxp, avg]
    powers2 = []
    #q = query(blocks[0])

    pivblock = blocks[0]

    #pag = q.aggregate(Sum('power'))
    d = len(blocks)

    m1 = list(range(1,13))
    q = 0
    blocknames = blocks_list#list(map(lambda x: x.blockid, blocks))

    percentages = []
    yearprod = []
    
    powers3 = 0

    guage = []
    chart_dict = {}

    m1 = list(range(1,13))
    
    try:
        
        power = query_for_month_many(blocknames, "2018", "1")

        #powers = get_aggs(q)
        #powers = json.dumps(get_aggs(q))

        powers3 = get_chart_data_m(blocknames, YEARS)
        yearprod = get_chart_data_whole_y(blocknames, YEARS)

        percentages = get_percentages_from_yearprod2(yearprod, blocks)

        if power == 0:
            percentages2 = []
        else:
            percentages2 = get_percentages_from_yearprod3(plant)
            guage = [[str(percentages2[0][-1]), percentages2[1][-1]]]

        years = YEARS[::-1]
        diaglist = [get_chart_data_b(blocknames, x) for x in years]

        #print(diaglist)



        for idx, diag in enumerate(diaglist):
            chart_dict[years[idx]] = diag

        #chartnums = list(range(0, len(diaglist)))

        #print(chart_dict)

        powers2 = diaglist[2]

        # = ["2018"] + list(map(lambda x: query_for_month(pivblock, "2018", x), m1))
        #powers2 = [query_for_month(q, "2018", "1")]
        
        d = len(powers)
    except TypeError:
        d = d

    #Entry.objects.filter(pub_date__date=datetime.date(2005, 1, 1))

    


    mhd = {}

    blocks_tmp_dict = list(map(model_to_dict, blocks_list))
    value_list = ["blockname", "blockdescription", "initialop", "endop", "chp", "state", "federalstate", "netpower"]
    key_list = ["energysource", "blockid", "plantid"]
    blocks_of_plant = create_blocks_dict(blocks_tmp_dict, value_list, key_list)

    blocks_header_list = ['BlockID', 'Kraftwerksname', 'Blockname', 'Inbetriebnahme', 'Abschaltung', 'KWK', 'Status', 'Bundesland', 'Nennleistung [in MW]']
    data_list = [plantid, plantname, block_count, le, tp]
    header_list = ['KraftwerkID', 'Kraftwerkname', 'Blockzahl', 'zuletzt erweitert', 'Gesamtleistung']
    context = {
        'data_list': zip(header_list, data_list),
        'header_list': blocks_header_list,
        'blocks_of_plant': blocks_of_plant,
        'blocknames': blocknames,
        'power' : power,
        'yearprod' : yearprod,
        'percentages': percentages,
        'percentages2': percentages2,
        'powers2' : powers2,
        'powers3' : powers3,
        'charts': chart_dict,
        'guage': guage,
        'plant_id': plantid,
        'q' : q,
        'd' : d,
    }
    return render(request, "plantmaster/plant2.html", context)


