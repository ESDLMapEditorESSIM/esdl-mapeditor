"""Definition of meta model 'esdl'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'esdl'
nsURI = 'http://www.tno.nl/esdl'
nsPrefix = 'esdl'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)
CommodityEnum = EEnum('CommodityEnum', literals=[
                      'UNDEFINED', 'ELECTRICITY', 'GAS', 'HEAT', 'H2', 'BIOGAS', 'CO2', 'ENERGY'])

AreaScopeEnum = EEnum('AreaScopeEnum', literals=['UNDEFINED', 'BUILDING', 'STREET', 'ZIPCODE', 'NEIGHBOURHOOD',
                                                 'DISTRICT', 'VILLAGE', 'CITY', 'MUNICIPALITY', 'REGION', 'PROVINCE', 'STATE', 'COUNTRY', 'CONTINENT'])

ProfileTypeEnum = EEnum('ProfileTypeEnum', literals=['UNDEFINED', 'SOLARIRRADIANCE_IN_W_PER_M2', 'WINDSPEED_IN_M_PER_S', 'STATEOFCHARGE_IN_WS', 'ENERGY_IN_WH', 'ENERGY_IN_KWH', 'ENERGY_IN_MWH', 'ENERGY_IN_GWH', 'ENERGY_IN_J', 'ENERGY_IN_KJ', 'ENERGY_IN_MJ', 'ENERGY_IN_GJ', 'ENERGY_IN_TJ',
                                                     'ENERGY_IN_PJ', 'TEMPERATURE_IN_C', 'TEMPERATURE_IN_K', 'POWER_IN_W', 'POWER_IN_KW', 'POWER_IN_MW', 'POWER_IN_GW', 'POWER_IN_TW', 'MONEY_IN_EUR', 'MONEY_IN_KEUR', 'MONEY_IN_MEUR', 'PERCENTAGE', 'MONEY_IN_EUR_PER_KW', 'MONEY_IN_EUR_PER_KWH', 'VOLUME_IN_M3', 'VOLUME_IN_LITERS'])

DurationUnitEnum = EEnum('DurationUnitEnum', literals=[
                         'SECOND', 'MINUTE', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'YEAR'])

BuildingTypeEnum = EEnum('BuildingTypeEnum', literals=['UNDEFINED', 'RESIDENTIAL', 'GATHERING', 'PRISON', 'HEALTHCARE',
                                                       'INDUSTRY', 'OFFICE', 'EDUCATION', 'SPORTS', 'SHOPPING', 'HOTEL', 'GREENHOUSE', 'UTILITY', 'OTHER'])

ConsTypeEnum = EEnum('ConsTypeEnum', literals=['PRIMARY', 'FINAL'])

SourceTypeEnum = EEnum('SourceTypeEnum', literals=[
                       'UNDEFINED', 'AIR', 'SUB_SURFACE', 'AQUIFER', 'SURFACE_WATER', 'HEAT_NETWORK'])

AggrTypeEnum = EEnum('AggrTypeEnum', literals=[
                     'UNDEFINED', 'NOT_AGGREGATED', 'PER_COMMODITY', 'TOTAL_ENERGY', 'TOTAL_CAPABILITY', 'PER_CAPIBILITY'])

AreaTypeEnum = EEnum('AreaTypeEnum', literals=['UNDEFINED', 'ROAD', 'RAILWAY', 'TERRAIN',
                                               'RURAL_AREA', 'BUILT', 'WATER', 'SEA', 'RIVER', 'CANAL', 'LAKE', 'LAND', 'PARCEL'])

HeatDemandTypeEnum = EEnum('HeatDemandTypeEnum', literals=[
                           'UNDEFINED', 'SPACE_HEATING', 'HOT_TAPWATER', 'SH_AND_HTW', 'OTHER'])

HousingTypeEnum = EEnum('HousingTypeEnum', literals=[
                        'UNDEFINED', 'OWNER_OCCUPIED_PROPERTY', 'PRIVATE_RENTAL', 'HOUSING_ASSOCIATION'])

RoofTypeEnum = EEnum('RoofTypeEnum', literals=[
                     'UNDEFINED', 'FLATROOF', 'SLANTEDROOF', 'COMBINATION'])

EnergyLabelEnum = EEnum('EnergyLabelEnum', literals=['UNDEFINED', 'LABEL_G', 'LABEL_F', 'LABEL_E',
                                                     'LABEL_D', 'LABEL_C', 'LABEL_B', 'LABEL_A', 'LABEL_AP', 'LABEL_APP', 'LABEL_APPP', 'LABEL_APPPP'])

ResidentialBuildingTypeEnum = EEnum('ResidentialBuildingTypeEnum', literals=['UNDEFINED', 'VRIJSTAANDE_WONING', 'TWEE_ONDER_EEN_KAP_WONING', 'RIJWONING',
                                                                             'MAISONNETTEWONING', 'GALERIJWONING', 'PORTIEKWONING', 'FLATWONING', 'TUSSENWONING', 'HOEKWONING', 'GALERIJCOMPLEX', 'APPARTEMENTENCOMPLEX', 'APPARTEMENT'])

PowerPlantFuelEnum = EEnum('PowerPlantFuelEnum', literals=[
                           'UNDEFINED', 'COAL', 'BLAST_FURNACE_GAS', 'NATURAL_GAS', 'URANIUM', 'HYDROGEN'])

SectorEnum = EEnum('SectorEnum', literals=[
                   'UNDEFINED', 'GEBOUWDE_OMGEVING', 'ZAKELIJKE_DIENSTVERLENING', 'INDUSTRIE', 'AGRO_TUINBOUW'])

RenewableTypeEnum = EEnum('RenewableTypeEnum', literals=['UNDEFINED', 'RENEWABLE', 'FOSSIL'])

StateOfMatterEnum = EEnum('StateOfMatterEnum', literals=['UNDEFINED', 'SOLID', 'LIQUID', 'GASEOUS'])

CostUnitEnum = EEnum('CostUnitEnum', literals=[
                     'UNDEFINED', 'MONEY_IN_EUR', 'MONEY_IN_KEUR', 'MONEY_IN_MEUR', 'MONEY_IN_EUR_PER_KW', 'MONEY_IN_EUR_PER_KWH'])

GeothermalSourceTypeEnum = EEnum('GeothermalSourceTypeEnum', literals=[
                                 'UNDEFINED', 'HEAT', 'ELECTRICITY'])

CHPTypeEnum = EEnum('CHPTypeEnum', literals=['UNDEFINED', 'STEG', 'GAS_TURBINE', 'GAS_MOTOR'])

GlassTypeEnum = EEnum('GlassTypeEnum', literals=[
                      'UNDEFINED', 'ENKEL_GLAS', 'DUBBEL_GLAS', 'HR_GLAS', 'HRP_GLAS', 'HRPP_GLAS', 'HRPPP_GLAS'])

VentilationTypeEnum = EEnum('VentilationTypeEnum', literals=[
                            'UNDEFINED', 'NATURAL', 'MECHANIC_IN', 'MECHANIC_OUT', 'MECHANIC_INOUT', 'BALANCED', 'BALANCED_WITH_HEATRECUPERATION'])

GasHeaterTypeEnum = EEnum('GasHeaterTypeEnum', literals=[
                          'UNDEFINED', 'CR', 'VR', 'HR100', 'HR104', 'HR107', 'HRE', 'HRWW'])

InhabitantsTypeEnum = EEnum('InhabitantsTypeEnum', literals=[
                            'UNDEFINED', 'ALLEENSTAAND', 'TWEEVERDIENERS', 'GEZIN_MET_KINDEREN', 'SENIOREN'])

AdditionalHeatingSourceTypeEnum = EEnum(
    'AdditionalHeatingSourceTypeEnum', literals=['NONE', 'ELECTRIC', 'GAS'])

GeothermalPotentialEnum = EEnum('GeothermalPotentialEnum', literals=['UNKNOWN', 'POSSIBLE', 'GOOD'])

GeothermalPowerEnum = EEnum('GeothermalPowerEnum', literals=[
                            'UNKNOWN', 'POSSIBLE_GT5MWTH', 'GOOD_GT5MWTH', 'GOOD_GT7P5MWTH', 'GOOD_GT10MWTH'])

ResidualHeatSourceTypeEnum = EEnum('ResidualHeatSourceTypeEnum', literals=[
                                   'UNDEFINED', 'INDUSTRIAL', 'DATACENTER', 'COOLING_HOUSE', 'OTHER'])

MobilityFuelTypeEnum = EEnum('MobilityFuelTypeEnum', literals=[
                             'UNDEFINED', 'PETROL', 'DIESEL', 'HYDROGEN', 'LPG', 'BIOFUEL', 'ELECTRICITY', 'OIL', 'LNG', 'KEROSENE'])

VehicleTypeEnum = EEnum('VehicleTypeEnum', literals=['UNDEFINED', 'CAR', 'TRUCK', 'VAN', 'BUS', 'METRO', 'TRAM', 'TRAIN', 'PASSENGER_TRAIN',
                                                     'FREIGHT_TRAIN', 'SCOOTER', 'MOTOR_CYCLE', 'NONROAD_VEHICLE', 'AGRARIAN_VEHICLE', 'BARGE', 'INTERNATIONAL_SHIPPING', 'AIRCRAFT', 'OTHER', 'TOTAL'])

MultiplierEnum = EEnum('MultiplierEnum', literals=[
                       'NONE', 'KILO', 'MEGA', 'GIGA', 'TERRA', 'PETA', 'MILLI', 'MICRO', 'NANO', 'PICO'])

PhysicalQuantityEnum = EEnum('PhysicalQuantityEnum', literals=['UNDEFINED', 'ENERGY', 'POWER', 'VOLTAGE', 'PRESSURE', 'TEMPERATURE',
                                                               'EMISSION', 'COST', 'TIME', 'LENGTH', 'DISTANCE', 'IRRADIANCE', 'SPEED', 'STATE_OF_CHARGE', 'VOLUME', 'AREA'])

UnitEnum = EEnum('UnitEnum', literals=['NONE', 'JOULE', 'WATTHOUR', 'WATT', 'VOLT', 'BAR', 'PSI', 'DEGREES_CELSIUS', 'KELVIN', 'GRAM', 'EURO', 'DOLLAR', 'SECOND',
                                       'MINUTE', 'QUARTER', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'YEAR', 'METRE', 'SQUARE_METRE', 'CUBIC_METRE', 'LITRE', 'WATTSECOND', 'ARE', 'HECTARE', 'PERCENT'])

TimeUnit = EEnum('TimeUnit', literals=['NONE', 'SECOND',
                                       'MINUTE', 'QUARTER', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'YEAR'])

GasConversionTypeEnum = EEnum('GasConversionTypeEnum', literals=['UNDEFINED', 'SMR', 'ATR'])

PVInstallationTypeEnum = EEnum('PVInstallationTypeEnum', literals=[
                               'UNDEFINED', 'ROOFTOP_PV', 'BUILDING_INTEGRATED_PV', 'WINDOW', 'ROAD', 'FIELD', 'WATER'])

WindTurbineTypeEnum = EEnum('WindTurbineTypeEnum', literals=[
                            'UNDEFINED', 'WIND_ON_LAND', 'WIND_AT_SEA', 'WIND_ON_COAST', 'WIND_ON_BUILDING'])

WaterToPowerTypeEnum = EEnum('WaterToPowerTypeEnum', literals=[
                             'UNDEFINED', 'HYDRO_POWER', 'WAVE_POWER', 'TIDAL_POWER', 'OSMOTIC_POWER'])

SolarCollectorTypeEnum = EEnum('SolarCollectorTypeEnum', literals=[
                               'UNDEFINED', 'ROOFTOP', 'BUILDING_INTEGRATED_SC', 'ROAD', 'FIELD', 'WATER'])

HeatRadiationDeviceTypeEnum = EEnum('HeatRadiationDeviceTypeEnum', literals=[
                                    'UNDEFINED', 'HT_RADIATOR', 'LT_RADIATOR', 'FLOOR_HEATING', 'WALL_HEATING', 'INFRARED_PANEL', 'AIR_HANDLING_UNIT'])

CoolingDeviceType = EEnum('CoolingDeviceType', literals=[
                          'UNDEFINED', 'FLOOR_COOLING', 'AIR_HANDLING_UNIT'])

RoomHeaterTypeEnum = EEnum('RoomHeaterTypeEnum', literals=[
                           'UNDEFINED', 'GAS_STOVE', 'WOOD_STOVE', 'ELECTRIC', 'INFRARED_PANEL'])

BiomassHeaterTypeEnum = EEnum('BiomassHeaterTypeEnum', literals=[
                              'UNDEFINED', 'FULLY_AUTOMATD', 'SEMI_AUTOMATED', 'PELLET_FIRED', 'CHP'])

UTESPotentialTypeEnum = EEnum('UTESPotentialTypeEnum', literals=[
                              'UNDEFINED', 'HEAT_OPEN', 'HEAT_CLOSED', 'COLD_OPEN', 'COLD_CLOSED'])

UTESTypeEnum = EEnum('UTESTypeEnum', literals=[
                     'UNDEFINED', 'AQUIFER_TES', 'BOREHOLE_TES', 'CAVERN_TES', 'OTHER'])

InterpolationMethodEnum = EEnum('InterpolationMethodEnum', literals=[
                                'UNDEFINED', 'NONE', 'LINEAR', 'CUBIC', 'NEAREST', 'PREVIOUS', 'NEXT', 'OTHER'])


class EnergySystem(EObject, metaclass=MetaEClass):
    """This is the main class to describe an EnergySystem in ESDL. Each energy system description should start with this class. More information about ESDL and the Energy System can be found in the gitbook at https://energytransition.gitbook.io/esdl/"""
    name = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    geographicalScope = EAttribute(eType=EString, derived=False, changeable=True)
    sector = EAttribute(eType=SectorEnum, derived=False, changeable=True, upper=-1)
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    measures = EReference(ordered=True, unique=True, containment=True)
    instance = EReference(ordered=True, unique=True, containment=True, upper=-1)
    energySystemInformation = EReference(ordered=True, unique=True, containment=True)
    parties = EReference(ordered=True, unique=True, containment=True)
    services = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, name=None, description=None, geographicalScope=None, sector=None, measures=None, instance=None, energySystemInformation=None, parties=None, services=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if geographicalScope is not None:
            self.geographicalScope = geographicalScope

        if sector:
            self.sector.extend(sector)

        if id is not None:
            self.id = id

        if measures is not None:
            self.measures = measures

        if instance:
            self.instance.extend(instance)

        if energySystemInformation is not None:
            self.energySystemInformation = energySystemInformation

        if parties is not None:
            self.parties = parties

        if services is not None:
            self.services = services


class Area(EObject, metaclass=MetaEClass):
    """The Area class represents a physical geographic area or a more abstract logical area. In both cases it is the 'asset container', in a sense that all assets within the area are contained by the Area instance."""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    scope = EAttribute(eType=AreaScopeEnum, derived=False, changeable=True,
                       default_value=AreaScopeEnum.UNDEFINED)
    type = EAttribute(eType=AreaTypeEnum, derived=False, changeable=True)
    geometryReference = EAttribute(eType=EString, derived=False, changeable=True)
    buildingDensity = EAttribute(eType=EDouble, derived=False, changeable=True)
    socialProperties = EReference(ordered=True, unique=True, containment=True)
    economicProperties = EReference(ordered=True, unique=True, containment=True)
    asset = EReference(ordered=True, unique=True, containment=True, upper=-1)
    area = EReference(ordered=True, unique=True, containment=True, upper=-1)
    containingArea = EReference(ordered=True, unique=True, containment=False)
    isOwnedBy = EReference(ordered=True, unique=True, containment=False)
    mobilityProperties = EReference(ordered=True, unique=True, containment=True)
    KPIs = EReference(ordered=True, unique=True, containment=True)
    potential = EReference(ordered=True, unique=True, containment=True, upper=-1)
    geometry = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, scope=None, type=None, socialProperties=None, economicProperties=None, asset=None, area=None, containingArea=None, isOwnedBy=None, geometryReference=None, mobilityProperties=None, buildingDensity=None, KPIs=None, potential=None, geometry=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if scope is not None:
            self.scope = scope

        if type is not None:
            self.type = type

        if geometryReference is not None:
            self.geometryReference = geometryReference

        if buildingDensity is not None:
            self.buildingDensity = buildingDensity

        if socialProperties is not None:
            self.socialProperties = socialProperties

        if economicProperties is not None:
            self.economicProperties = economicProperties

        if asset:
            self.asset.extend(asset)

        if area:
            self.area.extend(area)

        if containingArea is not None:
            self.containingArea = containingArea

        if isOwnedBy is not None:
            self.isOwnedBy = isOwnedBy

        if mobilityProperties is not None:
            self.mobilityProperties = mobilityProperties

        if KPIs is not None:
            self.KPIs = KPIs

        if potential:
            self.potential.extend(potential)

        if geometry is not None:
            self.geometry = geometry


@abstract
class Port(EObject, metaclass=MetaEClass):
    """Ports allow connections between EnergyAssets. Ports can be connected to one or more other ports. There are two types of ports: InPort and OutPort, which defines the primary direction of positive energy flow. InPorts can only be connected to OutPorts and vice versa."""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    maxPower = EAttribute(eType=EDouble, derived=False, changeable=True)
    simultaneousPower = EAttribute(eType=EDouble, derived=False, changeable=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    energyasset = EReference(ordered=True, unique=True, containment=False)
    profile = EReference(ordered=True, unique=True, containment=True)
    carrier = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, id=None, maxPower=None, energyasset=None, profile=None, carrier=None, simultaneousPower=None, name=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if maxPower is not None:
            self.maxPower = maxPower

        if simultaneousPower is not None:
            self.simultaneousPower = simultaneousPower

        if name is not None:
            self.name = name

        if energyasset is not None:
            self.energyasset = energyasset

        if profile is not None:
            self.profile = profile

        if carrier is not None:
            self.carrier = carrier


class EconomicProperties(EObject, metaclass=MetaEClass):
    """(experimental) Can be used to define the economic properties of an area"""
    averageIncome = EAttribute(eType=EDouble, derived=False, changeable=True)
    averageWOZvalue = EAttribute(eType=EDouble, derived=False, changeable=True)
    percentageOwnerOccupiedProperties = EAttribute(eType=EDouble, derived=False, changeable=True)
    percentageHousingAssociation = EAttribute(eType=EDouble, derived=False, changeable=True)
    percentagePrivateRental = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, averageIncome=None, averageWOZvalue=None, percentageOwnerOccupiedProperties=None, percentageHousingAssociation=None, percentagePrivateRental=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if averageIncome is not None:
            self.averageIncome = averageIncome

        if averageWOZvalue is not None:
            self.averageWOZvalue = averageWOZvalue

        if percentageOwnerOccupiedProperties is not None:
            self.percentageOwnerOccupiedProperties = percentageOwnerOccupiedProperties

        if percentageHousingAssociation is not None:
            self.percentageHousingAssociation = percentageHousingAssociation

        if percentagePrivateRental is not None:
            self.percentagePrivateRental = percentagePrivateRental


class SocialProperties(EObject, metaclass=MetaEClass):
    """(experimental) Can be used to define the social properties of an area"""
    socialCohesion = EAttribute(eType=EDouble, derived=False, changeable=True)
    populationDensity = EAttribute(eType=EInt, derived=False, changeable=True)
    numberOfInhabitants = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, socialCohesion=None, populationDensity=None, numberOfInhabitants=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if socialCohesion is not None:
            self.socialCohesion = socialCohesion

        if populationDensity is not None:
            self.populationDensity = populationDensity

        if numberOfInhabitants is not None:
            self.numberOfInhabitants = numberOfInhabitants


@abstract
class Item(EObject, metaclass=MetaEClass):
    """Class describing an abstract thing in an energy system. It is the parent of many other classes in ESDL, such as Assets, Services and Potentials. Parties can own Items"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    shortName = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    originalIdInSource = EAttribute(eType=EString, derived=False, changeable=True)
    isOwnedBy = EReference(ordered=True, unique=True, containment=False)
    dataSource = EReference(ordered=True, unique=True, containment=True)
    sector = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, id=None, name=None, shortName=None, isOwnedBy=None, description=None, originalIdInSource=None, dataSource=None, sector=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if shortName is not None:
            self.shortName = shortName

        if description is not None:
            self.description = description

        if originalIdInSource is not None:
            self.originalIdInSource = originalIdInSource

        if isOwnedBy is not None:
            self.isOwnedBy = isOwnedBy

        if dataSource is not None:
            self.dataSource = dataSource

        if sector is not None:
            self.sector = sector


class Measures(EObject, metaclass=MetaEClass):
    """Collection of measures that can be applied to an energy system"""
    asset = EReference(ordered=True, unique=True, containment=True, upper=-1)
    measuresCollection = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, asset=None, measuresCollection=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if asset:
            self.asset.extend(asset)

        if measuresCollection:
            self.measuresCollection.extend(measuresCollection)


class Instance(EObject, metaclass=MetaEClass):
    """Instances are used to represent different representations of the same EnergySystem. Most of the times only one Instance will be used. The primary use case for having more than one Instance is when you have different aggregations of the same EnergySystem in the same model (e.g. the same region on house level and aggregated on neighbourhood level). Another option would be to create different instances for different years (to describe the progress of the energy transition)."""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    detailLevel = EAttribute(eType=AreaScopeEnum, derived=False,
                             changeable=True, default_value=AreaScopeEnum.UNDEFINED)
    aggrType = EAttribute(eType=AggrTypeEnum, derived=False, changeable=True)
    area = EReference(ordered=True, unique=True, containment=True)
    date = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, description=None, detailLevel=None, aggrType=None, area=None, date=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if detailLevel is not None:
            self.detailLevel = detailLevel

        if aggrType is not None:
            self.aggrType = aggrType

        if area is not None:
            self.area = area

        if date is not None:
            self.date = date


class Carriers(EObject, metaclass=MetaEClass):
    """Collection of carriers as part of the Energy System Information. Both energy carriers and commodities."""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    carrier = EReference(ordered=True, unique=True, containment=True, upper=-1)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, carrier=None, dataSource=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if carrier:
            self.carrier.extend(carrier)

        if dataSource is not None:
            self.dataSource = dataSource


class EnergySystemInformation(EObject, metaclass=MetaEClass):
    """Describes reusable information of the energy system, that other classes can refer to in this energy system, such as carriers, profiles, data sources, quantity and units."""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    carriers = EReference(ordered=True, unique=True, containment=True)
    profiles = EReference(ordered=True, unique=True, containment=True)
    dataSources = EReference(ordered=True, unique=True, containment=True)
    mobilityFuelInformation = EReference(ordered=True, unique=True, containment=True)
    quantityAndUnits = EReference(ordered=True, unique=True, containment=True)
    sectors = EReference(ordered=True, unique=True, containment=True)
    buildingUsageInformation = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, carriers=None, profiles=None, dataSources=None, mobilityFuelInformation=None, quantityAndUnits=None, sectors=None, id=None, buildingUsageInformation=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if carriers is not None:
            self.carriers = carriers

        if profiles is not None:
            self.profiles = profiles

        if dataSources is not None:
            self.dataSources = dataSources

        if mobilityFuelInformation is not None:
            self.mobilityFuelInformation = mobilityFuelInformation

        if quantityAndUnits is not None:
            self.quantityAndUnits = quantityAndUnits

        if sectors is not None:
            self.sectors = sectors

        if buildingUsageInformation is not None:
            self.buildingUsageInformation = buildingUsageInformation


@abstract
class GenericProfile(EObject, metaclass=MetaEClass):
    """All profiles should describe these fields: a name and a ProfileType. There are two different profile types: static, with static values stored in the ESDL model itself. And External, which allows you to refer to an externally defined profile (e.g. in an Energy Information System or a timeseries database)"""
    name = EAttribute(eType=EString, derived=False, changeable=True)
    profileType = EAttribute(eType=ProfileTypeEnum, derived=False,
                             changeable=True, default_value=ProfileTypeEnum.UNDEFINED)
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    interpolationMethod = EAttribute(eType=InterpolationMethodEnum, derived=False,
                                     changeable=True, default_value=InterpolationMethodEnum.UNDEFINED)
    dataSource = EReference(ordered=True, unique=True, containment=True)
    profileQuantityAndUnit = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, name=None, profileType=None, id=None, dataSource=None, profileQuantityAndUnit=None, interpolationMethod=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if profileType is not None:
            self.profileType = profileType

        if id is not None:
            self.id = id

        if interpolationMethod is not None:
            self.interpolationMethod = interpolationMethod

        if dataSource is not None:
            self.dataSource = dataSource

        if profileQuantityAndUnit is not None:
            self.profileQuantityAndUnit = profileQuantityAndUnit

    def getProfile(self, from_=None, to=None, aggregationPrecision=None):

        raise NotImplementedError('operation getProfile(...) not yet implemented')

    def setProfile(self, profileElementList=None):

        raise NotImplementedError('operation setProfile(...) not yet implemented')


class ProfileElement(EObject, metaclass=MetaEClass):
    """ProfileElement describes a single profile element describing a range and a value which is valid for this range. From-field is inclusive, To-field is exclusive, allowing you to describe ranges such as 1-1-2017T00:00:00.000 to 1-1-2018T00:00:00.000 instead of 31-12-2017T23:59:59:999. The to-field may be ommitted, meaning this value is valid for all time after the specified to-datetime.
Examples: The heat demand of a municipality in 2013 is 20 PJ. The range you define is then from 1-1-2013T to 1-1-2014T and the value 20 and ProfileType ENERGY_IN_PJ"""
    from_ = EAttribute(eType=EDate, derived=False, changeable=True)
    to = EAttribute(eType=EDate, derived=False, changeable=True)
    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, from_=None, to=None, value=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if from_ is not None:
            self.from_ = from_

        if to is not None:
            self.to = to

        if value is not None:
            self.value = value


@abstract
class GenericDistribution(EObject, metaclass=MetaEClass):
    """Abstract class to represent different types of distributions"""
    name = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, name=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name


class Percentile(EObject, metaclass=MetaEClass):
    """Defines the percentile of a percentile distribution"""
    percentile = EAttribute(eType=EInt, derived=False, changeable=True)
    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, percentile=None, value=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if percentile is not None:
            self.percentile = percentile

        if value is not None:
            self.value = value


class CostInformation(EObject, metaclass=MetaEClass):
    """Describes the costs to acquire, install and maintain a certain asset."""
    investmentCosts = EReference(ordered=True, unique=True, containment=True)
    installationCosts = EReference(ordered=True, unique=True, containment=True)
    fixedOperationalAndMaintenanceCosts = EReference(ordered=True, unique=True, containment=True)
    marginalCosts = EReference(ordered=True, unique=True, containment=True)
    variableOperationalAndMaintenanceCosts = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, investmentCosts=None, installationCosts=None, fixedOperationalAndMaintenanceCosts=None, marginalCosts=None, variableOperationalAndMaintenanceCosts=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if investmentCosts is not None:
            self.investmentCosts = investmentCosts

        if installationCosts is not None:
            self.installationCosts = installationCosts

        if fixedOperationalAndMaintenanceCosts is not None:
            self.fixedOperationalAndMaintenanceCosts = fixedOperationalAndMaintenanceCosts

        if marginalCosts is not None:
            self.marginalCosts = marginalCosts

        if variableOperationalAndMaintenanceCosts is not None:
            self.variableOperationalAndMaintenanceCosts = variableOperationalAndMaintenanceCosts


class StringPerc(EObject, metaclass=MetaEClass):
    """Defines a label and a percentage, used in StringLabelDistribution"""
    label = EAttribute(eType=EString, derived=False, changeable=True)
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, label=None, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if label is not None:
            self.label = label

        if percentage is not None:
            self.percentage = percentage


class EnergyLabelPerc(EObject, metaclass=MetaEClass):
    """Defines an energy label and a percentage, used in EnergyLabelDistribution"""
    energyLabel = EAttribute(eType=EnergyLabelEnum, derived=False, changeable=True)
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, energyLabel=None, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if energyLabel is not None:
            self.energyLabel = energyLabel

        if percentage is not None:
            self.percentage = percentage


@abstract
class FromToPerc(EObject, metaclass=MetaEClass):
    """Defines a range and a percentage, used in the FromToDistribution class"""
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if percentage is not None:
            self.percentage = percentage


class PItemStat(EObject, metaclass=MetaEClass):
    """(experimental) Used to define statistical information"""
    value = EAttribute(eType=EDouble, derived=False, changeable=True)
    sigma = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, value=None, sigma=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if value is not None:
            self.value = value

        if sigma is not None:
            self.sigma = sigma


@abstract
class AbstractVariance(EObject, metaclass=MetaEClass):
    """(experimental) Used to define statistical information"""

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()


class Party(EObject, metaclass=MetaEClass):
    """Defines a stakeholder in the energy system, to represent ownership"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    shortName = EAttribute(eType=EString, derived=False, changeable=True)
    owns = EReference(ordered=True, unique=True, containment=False, upper=-1)
    ownsArea = EReference(ordered=True, unique=True, containment=False, upper=-1)
    sector = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, owns=None, id=None, name=None, shortName=None, ownsArea=None, sector=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if shortName is not None:
            self.shortName = shortName

        if owns:
            self.owns.extend(owns)

        if ownsArea:
            self.ownsArea.extend(ownsArea)

        if sector is not None:
            self.sector = sector


@abstract
class Geometry(EObject, metaclass=MetaEClass):
    """Abstract class to define the shape/location of an asset or area. Parent class of e.g. Point, Line and Polygon"""
    CRS = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, CRS=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if CRS is not None:
            self.CRS = CRS


@abstract
class Carrier(EObject, metaclass=MetaEClass):
    """Abstract class to define the carrier of energy, e.g. a energy carrier or a commodity (such as electricity)"""
    name = EAttribute(eType=EString, derived=False, changeable=True)
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    cost = EReference(ordered=True, unique=True, containment=True)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, name=None, id=None, cost=None, dataSource=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if id is not None:
            self.id = id

        if cost is not None:
            self.cost = cost

        if dataSource is not None:
            self.dataSource = dataSource


class Duration(EObject, metaclass=MetaEClass):
    """Defines the duration of a profile query"""
    value = EAttribute(eType=ELong, derived=False, changeable=True)
    durationUnit = EAttribute(eType=DurationUnitEnum, derived=False,
                              changeable=True, default_value=DurationUnitEnum.SECOND)

    def __init__(self, *, value=None, durationUnit=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if value is not None:
            self.value = value

        if durationUnit is not None:
            self.durationUnit = durationUnit


class Profiles(EObject, metaclass=MetaEClass):
    """Container for profiles in the Energy System Information where other profiles can refer to"""
    profile = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, profile=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if profile:
            self.profile.extend(profile)


class Parties(EObject, metaclass=MetaEClass):
    """Container for parties that have a role in the energy system"""
    party = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, party=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if party:
            self.party.extend(party)


class DataSources(EObject, metaclass=MetaEClass):
    """Collection of datasources used in the energy system"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    dataSource = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, dataSource=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if dataSource:
            self.dataSource.extend(dataSource)


class SubPolygon(EObject, metaclass=MetaEClass):
    """Part of a Polygon used to describe the internal or external boundary"""
    point = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, point=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if point:
            self.point.extend(point)


class MobilityFuelInformation(EObject, metaclass=MetaEClass):
    """Collection of information about vehicles, fuels and efficiency"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    vehicleFuelEfficiency = EReference(ordered=True, unique=True, containment=True, upper=-1)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, vehicleFuelEfficiency=None, dataSource=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if vehicleFuelEfficiency:
            self.vehicleFuelEfficiency.extend(vehicleFuelEfficiency)

        if dataSource is not None:
            self.dataSource = dataSource


class VehicleFuelEfficiency(EObject, metaclass=MetaEClass):
    """Information about vehicles, fuels and efficiency, used in MobilityFuelInformation"""
    vehicleType = EAttribute(eType=VehicleTypeEnum, derived=False, changeable=True)
    fuel = EAttribute(eType=MobilityFuelTypeEnum, derived=False, changeable=True)
    efficiency = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, vehicleType=None, fuel=None, efficiency=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if vehicleType is not None:
            self.vehicleType = vehicleType

        if fuel is not None:
            self.fuel = fuel

        if efficiency is not None:
            self.efficiency = efficiency


class MobilityProperties(EObject, metaclass=MetaEClass):
    """(experimental) Can be used to define the mobility properties of an area"""
    numberOfVehicles = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, numberOfVehicles=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if numberOfVehicles is not None:
            self.numberOfVehicles = numberOfVehicles


class NumberOfVehicles(EObject, metaclass=MetaEClass):
    """(experimental) Provides the ability to define the number of vehicles of an area"""
    vehicleCount = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, vehicleCount=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if vehicleCount:
            self.vehicleCount.extend(vehicleCount)


class VehicleCount(EObject, metaclass=MetaEClass):
    """(experimental) Defines the number of vehicles per vehicle type"""
    type = EAttribute(eType=VehicleTypeEnum, derived=False, changeable=True)
    count = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, type=None, count=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if type is not None:
            self.type = type

        if count is not None:
            self.count = count


class Services(EObject, metaclass=MetaEClass):
    """Defines a collection of logical services used in the energy system, e.g. Demand-Response, Aggregator services, Energy markets and control strategies."""
    service = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, service=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if service:
            self.service.extend(service)


@abstract
class AbstractDataSource(EObject, metaclass=MetaEClass):
    """Abstract class to describe data sources or references to data sources"""

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()


class KPIs(EObject, metaclass=MetaEClass):
    """Collection of key performance indicators of areas or assets"""
    id = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    kpi = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, kpi=None, id=None, description=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if description is not None:
            self.description = description

        if kpi:
            self.kpi.extend(kpi)


@abstract
class KPI(EObject, metaclass=MetaEClass):
    """Defines a key performance indicator (KPI)"""
    id = EAttribute(eType=EString, derived=False, changeable=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    quantityAndUnit = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, quantityAndUnit=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if quantityAndUnit is not None:
            self.quantityAndUnit = quantityAndUnit


class QuantityAndUnits(EObject, metaclass=MetaEClass):
    """Collection of QuantityAndUnitTypes defined in the EnergySystemInformation section"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    quantityAndUnit = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, quantityAndUnit=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if quantityAndUnit:
            self.quantityAndUnit.extend(quantityAndUnit)


@abstract
class AbstractQuantityAndUnit(EObject, metaclass=MetaEClass):
    """Abstract class to describe QuantityAndUnitTypes or references to these"""

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()


@abstract
class Parameters(EObject, metaclass=MetaEClass):
    """Used to describe properties of an EnergyMarket"""
    name = EAttribute(eType=EString, derived=False, changeable=True)
    parameterUnit = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, name=None, parameterUnit=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if parameterUnit is not None:
            self.parameterUnit = parameterUnit


class MeasuresCombination(EObject, metaclass=MetaEClass):
    """A combination of measures with single cost information that can be applied to an energy system. E.g. a combination of insulation and a heat pump. For a single measure (e.g. a PV installation) use Measures"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    asset = EReference(ordered=True, unique=True, containment=True, upper=-1)
    costInformation = EReference(ordered=True, unique=True, containment=True)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, asset=None, costInformation=None, description=None, dataSource=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if asset:
            self.asset.extend(asset)

        if costInformation is not None:
            self.costInformation = costInformation

        if dataSource is not None:
            self.dataSource = dataSource


class Sectors(EObject, metaclass=MetaEClass):
    """Collection of sectors. Both Party and Item can link to a sector"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    sector = EReference(ordered=True, unique=True, containment=True, upper=-1)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, sector=None, dataSource=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if sector:
            self.sector.extend(sector)

        if dataSource is not None:
            self.dataSource = dataSource


class Sector(EObject, metaclass=MetaEClass):
    """Defines a sector. Can be used for the Standaard Bedrijfsindeling (SBI) of the CBS in the Netherlands"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    code = EAttribute(eType=EString, derived=False, changeable=True)
    dataSource = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, description=None, dataSource=None, code=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if code is not None:
            self.code = code

        if dataSource is not None:
            self.dataSource = dataSource


@abstract
class AbstractInstanceDate(EObject, metaclass=MetaEClass):
    """Abstract class to define the date or period of the validity of the data that is used in this instance """

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()


class WeekSchedule(EObject, metaclass=MetaEClass):

    mon = EReference(ordered=True, unique=True, containment=True)
    tue = EReference(ordered=True, unique=True, containment=True)
    wed = EReference(ordered=True, unique=True, containment=True)
    thu = EReference(ordered=True, unique=True, containment=True)
    fri = EReference(ordered=True, unique=True, containment=True)
    sat = EReference(ordered=True, unique=True, containment=True)
    sun = EReference(ordered=True, unique=True, containment=True)
    weekdays = EReference(ordered=True, unique=True, containment=True)
    weekenddays = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, mon=None, tue=None, wed=None, thu=None, fri=None, sat=None, sun=None, weekdays=None, weekenddays=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if mon is not None:
            self.mon = mon

        if tue is not None:
            self.tue = tue

        if wed is not None:
            self.wed = wed

        if thu is not None:
            self.thu = thu

        if fri is not None:
            self.fri = fri

        if sat is not None:
            self.sat = sat

        if sun is not None:
            self.sun = sun

        if weekdays is not None:
            self.weekdays = weekdays

        if weekenddays is not None:
            self.weekenddays = weekenddays


class DaySchedule(EObject, metaclass=MetaEClass):

    event = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, event=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if event:
            self.event.extend(event)


class Event(EObject, metaclass=MetaEClass):

    id = EAttribute(eType=EString, derived=False, changeable=True)
    time = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, id=None, time=None, description=None, value=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if time is not None:
            self.time = time

        if description is not None:
            self.description = description

        if value is not None:
            self.value = value


@abstract
class AbstractBuildingUsage(EObject, metaclass=MetaEClass):

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()


class BuildingUsageInformation(EObject, metaclass=MetaEClass):

    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    buildingUsage = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, buildingUsage=None, id=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if buildingUsage:
            self.buildingUsage.extend(buildingUsage)


class BuildingTypePercentage(EObject, metaclass=MetaEClass):

    buildingType = EAttribute(eType=BuildingTypeEnum, derived=False, changeable=True)
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, buildingType=None, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if buildingType is not None:
            self.buildingType = buildingType

        if percentage is not None:
            self.percentage = percentage


class ResidentialBuildingTypePercentage(EObject, metaclass=MetaEClass):

    residentialBuildingType = EAttribute(
        eType=ResidentialBuildingTypeEnum, derived=False, changeable=True)
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, residentialBuildingType=None, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if residentialBuildingType is not None:
            self.residentialBuildingType = residentialBuildingType

        if percentage is not None:
            self.percentage = percentage


class HousingTypePercentage(EObject, metaclass=MetaEClass):

    housingType = EAttribute(eType=HousingTypeEnum, derived=False, changeable=True)
    percentage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, housingType=None, percentage=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if housingType is not None:
            self.housingType = housingType

        if percentage is not None:
            self.percentage = percentage


class InPort(Port):
    """Represents a port with a positive energy direction into the asset, e.g. for a Consumer. See Port for more details"""
    connectedTo = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, connectedTo=None, **kwargs):

        super().__init__(**kwargs)

        if connectedTo:
            self.connectedTo.extend(connectedTo)


class OutPort(Port):
    """Represents a port with a positive energy direction out of the asset, e.g. for a Producer. See Port for more details"""
    connectedTo = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, connectedTo=None, **kwargs):

        super().__init__(**kwargs)

        if connectedTo:
            self.connectedTo.extend(connectedTo)


@abstract
class Asset(Item):
    """Assets are all physical thing in the EnergySystem. Assets can have a location, a geometry, commissioning and decommissioning dates, cost information (investment, installation and operation and maintenance costs)."""
    surfaceArea = EAttribute(eType=EInt, derived=False, changeable=True)
    commissioningDate = EAttribute(eType=EDate, derived=False, changeable=True)
    decommissioningDate = EAttribute(eType=EDate, derived=False, changeable=True)
    owner = EAttribute(eType=EString, derived=False, changeable=True)
    technicalLifetime = EAttribute(eType=EDouble, derived=False, changeable=True)
    aggregated = EAttribute(eType=EBoolean, derived=False, changeable=True)
    aggregationCount = EAttribute(eType=EInt, derived=False, changeable=True, default_value=1)
    installationDuration = EAttribute(eType=EDouble, derived=False, changeable=True)
    area = EReference(ordered=True, unique=True, containment=False)
    containingBuilding = EReference(ordered=True, unique=True, containment=False)
    geometry = EReference(ordered=True, unique=True, containment=True)
    costInformation = EReference(ordered=True, unique=True, containment=True)
    KPIs = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, surfaceArea=None, commissioningDate=None, decommissioningDate=None, owner=None, area=None, containingBuilding=None, geometry=None, costInformation=None, technicalLifetime=None, aggregated=None, aggregationCount=None, installationDuration=None, KPIs=None, **kwargs):

        super().__init__(**kwargs)

        if surfaceArea is not None:
            self.surfaceArea = surfaceArea

        if commissioningDate is not None:
            self.commissioningDate = commissioningDate

        if decommissioningDate is not None:
            self.decommissioningDate = decommissioningDate

        if owner is not None:
            self.owner = owner

        if technicalLifetime is not None:
            self.technicalLifetime = technicalLifetime

        if aggregated is not None:
            self.aggregated = aggregated

        if aggregationCount is not None:
            self.aggregationCount = aggregationCount

        if installationDuration is not None:
            self.installationDuration = installationDuration

        if area is not None:
            self.area = area

        if containingBuilding is not None:
            self.containingBuilding = containingBuilding

        if geometry is not None:
            self.geometry = geometry

        if costInformation is not None:
            self.costInformation = costInformation

        if KPIs is not None:
            self.KPIs = KPIs


class Point(Geometry):
    """Describes a point geometry, which can be used for giving assets a location on a map"""
    lat = EAttribute(eType=EDouble, derived=False, changeable=True)
    lon = EAttribute(eType=EDouble, derived=False, changeable=True)
    elevation = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, lat=None, lon=None, elevation=None, **kwargs):

        super().__init__(**kwargs)

        if lat is not None:
            self.lat = lat

        if lon is not None:
            self.lon = lon

        if elevation is not None:
            self.elevation = elevation


class Polygon(Geometry):
    """Describes a polygon geometry, which can be used for defining the shape of an area or building"""
    exterior = EReference(ordered=True, unique=True, containment=True)
    interior = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, exterior=None, interior=None, **kwargs):

        super().__init__(**kwargs)

        if exterior is not None:
            self.exterior = exterior

        if interior:
            self.interior.extend(interior)


@abstract
class Service(Item):
    """Abstract class to represent logical entities in the energy system, e.g. demand response services, energy markets, etc."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class Potential(Item):
    """Abstract class that represents energy potentials in an area, like wind potential, geothermal potential, residual heat source potential, etc."""
    geometryReference = EAttribute(eType=EString, derived=False, changeable=True)
    aggregated = EAttribute(eType=EBoolean, derived=False, changeable=True, default_value=False)
    aggregationCount = EAttribute(eType=EInt, derived=False, changeable=True, default_value=1)
    geometry = EReference(ordered=True, unique=True, containment=True)
    quantityAndUnit = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, geometry=None, geometryReference=None, quantityAndUnit=None, aggregated=None, aggregationCount=None, **kwargs):

        super().__init__(**kwargs)

        if geometryReference is not None:
            self.geometryReference = geometryReference

        if aggregated is not None:
            self.aggregated = aggregated

        if aggregationCount is not None:
            self.aggregationCount = aggregationCount

        if geometry is not None:
            self.geometry = geometry

        if quantityAndUnit is not None:
            self.quantityAndUnit = quantityAndUnit


class EnergyCarrier(Carrier):
    """Defines a carrier of energy with its emission and energy content properties"""
    energyContent = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    emission = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    energyCarrierType = EAttribute(eType=RenewableTypeEnum, derived=False, changeable=True)
    stateOfMatter = EAttribute(eType=StateOfMatterEnum, derived=False, changeable=True)
    energyContentUnit = EReference(ordered=True, unique=True, containment=True)
    emissionUnit = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, energyContent=None, emission=None, energyCarrierType=None, stateOfMatter=None, energyContentUnit=None, emissionUnit=None, **kwargs):

        super().__init__(**kwargs)

        if energyContent is not None:
            self.energyContent = energyContent

        if emission is not None:
            self.emission = emission

        if energyCarrierType is not None:
            self.energyCarrierType = energyCarrierType

        if stateOfMatter is not None:
            self.stateOfMatter = stateOfMatter

        if energyContentUnit is not None:
            self.energyContentUnit = energyContentUnit

        if emissionUnit is not None:
            self.emissionUnit = emissionUnit


@abstract
class StaticProfile(GenericProfile):
    """Stores the profile in the ESDL model itself, in contrast with an external profile, which refers to an external source for a profile"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class ExternalProfile(GenericProfile):
    """ExternalProfile allows to refer to an externally defined profile. Common uses are a profile defined in a (timeseries) database such as InfluxDB.
It allows you to specify a multiplier to scale the supplied external profile by a certain factor (e.g. when using NEDU profiles). Default the multiplier is '1'."""
    multiplier = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=1.0)

    def __init__(self, *, multiplier=None, **kwargs):

        super().__init__(**kwargs)

        if multiplier is not None:
            self.multiplier = multiplier


class PercentileDistribution(GenericDistribution):
    """Defines a distribution in terms of percentiles"""
    percentile = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, percentile=None, **kwargs):

        super().__init__(**kwargs)

        if percentile:
            self.percentile.extend(percentile)


@abstract
class LabelDistribution(GenericDistribution):
    """Abstract class to define a distribution with labels"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class SymetricVariance(AbstractVariance):
    """(experimental) Used to define statistical information"""
    sigma = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, sigma=None, **kwargs):

        super().__init__(**kwargs)

        if sigma is not None:
            self.sigma = sigma


class AssymetricVariance(AbstractVariance):
    """(experimental) Used to define statistical information"""
    sigmaMin = EAttribute(eType=EDouble, derived=False, changeable=True)
    sigmaPlus = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, sigmaMin=None, sigmaPlus=None, **kwargs):

        super().__init__(**kwargs)

        if sigmaMin is not None:
            self.sigmaMin = sigmaMin

        if sigmaPlus is not None:
            self.sigmaPlus = sigmaPlus


class DoubleAssymetricVariance(AbstractVariance):
    """(experimental) Used to define statistical information"""
    plus34perc = EAttribute(eType=EDouble, derived=False, changeable=True)
    plus48perc = EAttribute(eType=EDouble, derived=False, changeable=True)
    min34perc = EAttribute(eType=EDouble, derived=False, changeable=True)
    min48perc = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, plus34perc=None, plus48perc=None, min34perc=None, min48perc=None, **kwargs):

        super().__init__(**kwargs)

        if plus34perc is not None:
            self.plus34perc = plus34perc

        if plus48perc is not None:
            self.plus48perc = plus48perc

        if min34perc is not None:
            self.min34perc = min34perc

        if min48perc is not None:
            self.min48perc = min48perc


class Line(Geometry):
    """Describes a line geometry based on a list of points, which can be used to define the shape of pipes and cables"""
    point = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, point=None, **kwargs):

        super().__init__(**kwargs)

        if point:
            self.point.extend(point)


@abstract
class Commodity(Carrier):
    """Abstract class for commodities"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class DataSource(AbstractDataSource):
    """A DataSource describes the source of the piece of information used in the energy system. E.g. a profile from NEDU or typical parameters of an Asset"""
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    reference = EAttribute(eType=EString, derived=False, changeable=True)
    attribution = EAttribute(eType=EString, derived=False, changeable=True)
    releaseDate = EAttribute(eType=EDate, derived=False, changeable=True)
    version = EAttribute(eType=EString, derived=False, changeable=True)
    licence = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, id=None, name=None, description=None, reference=None, attribution=None, releaseDate=None, version=None, licence=None, **kwargs):

        super().__init__(**kwargs)

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if reference is not None:
            self.reference = reference

        if attribution is not None:
            self.attribution = attribution

        if releaseDate is not None:
            self.releaseDate = releaseDate

        if version is not None:
            self.version = version

        if licence is not None:
            self.licence = licence


class MultiPolygon(Geometry):
    """Collection of Polygons"""
    polygon = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, polygon=None, **kwargs):

        super().__init__(**kwargs)

        if polygon:
            self.polygon.extend(polygon)


class QuantityAndUnitType(AbstractQuantityAndUnit):
    """Defines the quantity and its unit for a specific parameter. Used in e.g. profiles and KPIs. For example Energy in Joules or CO2 emission in kton."""
    physicalQuantity = EAttribute(eType=PhysicalQuantityEnum, derived=False, changeable=True)
    multiplier = EAttribute(eType=MultiplierEnum, derived=False, changeable=True)
    unit = EAttribute(eType=UnitEnum, derived=False, changeable=True)
    perMultiplier = EAttribute(eType=MultiplierEnum, derived=False, changeable=True)
    perUnit = EAttribute(eType=UnitEnum, derived=False, changeable=True)
    description = EAttribute(eType=EString, derived=False, changeable=True)
    perTimeUnit = EAttribute(eType=TimeUnit, derived=False, changeable=True)
    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)

    def __init__(self, *, physicalQuantity=None, multiplier=None, unit=None, perMultiplier=None, perUnit=None, description=None, perTimeUnit=None, id=None, **kwargs):

        super().__init__(**kwargs)

        if physicalQuantity is not None:
            self.physicalQuantity = physicalQuantity

        if multiplier is not None:
            self.multiplier = multiplier

        if unit is not None:
            self.unit = unit

        if perMultiplier is not None:
            self.perMultiplier = perMultiplier

        if perUnit is not None:
            self.perUnit = perUnit

        if description is not None:
            self.description = description

        if perTimeUnit is not None:
            self.perTimeUnit = perTimeUnit

        if id is not None:
            self.id = id


class DataSourceReference(AbstractDataSource):
    """Defines a reference to a datasource, defined in the collection of DataSources (as part of the EnergySystemInformation)"""
    reference = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, reference=None, **kwargs):

        super().__init__(**kwargs)

        if reference is not None:
            self.reference = reference


class QuantityAndUnitReference(AbstractQuantityAndUnit):
    """Defines a reference to a QuantityAndUnitType defined in the collection of QuantityAndUnits (as part of the EnergySystemInformation)"""
    reference = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, reference=None, **kwargs):

        super().__init__(**kwargs)

        if reference is not None:
            self.reference = reference


class StringParameter(Parameters):
    """Defines a parameter of type String"""
    value = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class DoubleParameter(Parameters):
    """Defines a parameter of type Double"""
    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class IntegerParameter(Parameters):
    """Defines a parameter of type Integer"""
    value = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class BooleanParameter(Parameters):
    """Defines a parameter of type Boolean"""
    value = EAttribute(eType=EBoolean, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class MultiLine(Geometry):
    """Defines a collection of lines"""
    line = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, line=None, **kwargs):

        super().__init__(**kwargs)

        if line:
            self.line.extend(line)


class InstanceDate(AbstractInstanceDate):
    """Describes the date of the validity of the data that is used in this instance """
    date = EAttribute(eType=EDate, derived=False, changeable=True)

    def __init__(self, *, date=None, **kwargs):

        super().__init__(**kwargs)

        if date is not None:
            self.date = date


class InstancePeriod(AbstractInstanceDate):
    """Describes the period of the validity of the data that is used in this instance """
    fromDate = EAttribute(eType=EDate, derived=False, changeable=True)
    toDate = EAttribute(eType=EDate, derived=False, changeable=True)

    def __init__(self, *, fromDate=None, toDate=None, **kwargs):

        super().__init__(**kwargs)

        if fromDate is not None:
            self.fromDate = fromDate

        if toDate is not None:
            self.toDate = toDate


class WKT(Geometry):
    """Well-Known Text (see https://en.wikipedia.org/wiki/Well-known_text)"""
    value = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class WKB(Geometry):
    """Well-Known Binary (See https://en.wikipedia.org/wiki/Well-known_text#Well-known_binary)"""
    value = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class BuildingUsage(AbstractBuildingUsage):

    id = EAttribute(eType=EString, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, derived=False, changeable=True)
    coolingSetpoints = EReference(ordered=True, unique=True, containment=True)
    heatingSetpoints = EReference(ordered=True, unique=True, containment=True)
    openingHours = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, id=None, name=None, coolingSetpoints=None, heatingSetpoints=None, openingHours=None, **kwargs):

        super().__init__(**kwargs)

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if coolingSetpoints is not None:
            self.coolingSetpoints = coolingSetpoints

        if heatingSetpoints is not None:
            self.heatingSetpoints = heatingSetpoints

        if openingHours is not None:
            self.openingHours = openingHours


class BuildingUsageReference(AbstractBuildingUsage):

    reference = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, reference=None, **kwargs):

        super().__init__(**kwargs)

        if reference is not None:
            self.reference = reference


class DoubleKPI(KPI):

    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class StringKPI(KPI):

    value = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class IntKPI(KPI):

    value = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class FromToIntPerc(FromToPerc):

    from_ = EAttribute(eType=EInt, derived=False, changeable=True)
    to = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, from_=None, to=None, **kwargs):

        super().__init__(**kwargs)

        if from_ is not None:
            self.from_ = from_

        if to is not None:
            self.to = to


class FromToDoublePerc(FromToPerc):

    from_ = EAttribute(eType=EDouble, derived=False, changeable=True)
    to = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, from_=None, to=None, **kwargs):

        super().__init__(**kwargs)

        if from_ is not None:
            self.from_ = from_

        if to is not None:
            self.to = to


class Material(Carrier):
    """Class for describing materials other than carriers (e.g. water as an input for an electrolyzer)"""
    density = EAttribute(eType=EDouble, derived=False, changeable=True)
    stateOfMatter = EAttribute(eType=StateOfMatterEnum, derived=False,
                               changeable=True, default_value=StateOfMatterEnum.UNDEFINED)

    def __init__(self, *, density=None, stateOfMatter=None, **kwargs):

        super().__init__(**kwargs)

        if density is not None:
            self.density = density

        if stateOfMatter is not None:
            self.stateOfMatter = stateOfMatter


@abstract
class EnergyAsset(Asset):
    """An abstract class that describes a connectable Asset using ports. EnergyAssets main subclasses contain the 5 capability type: Producer, Consumer, Storage, Conversion and Transport """
    port = EReference(ordered=True, unique=True, containment=True, upper=-1)
    controlStrategy = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, port=None, controlStrategy=None, **kwargs):

        super().__init__(**kwargs)

        if port:
            self.port.extend(port)

        if controlStrategy is not None:
            self.controlStrategy = controlStrategy


class Insulation(Asset):
    """Describes insulation that can be added to a building. The relation with the heat consumption is not defined and requires manual modelling"""
    thermalInsulation = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, thermalInsulation=None, **kwargs):

        super().__init__(**kwargs)

        if thermalInsulation is not None:
            self.thermalInsulation = thermalInsulation


class LegalArea(Potential):
    """Used to define an area in which its purpose is defined by legal authorities, such as restricted areas. E.g. in areas where water is extracted, it is not allowed to plan new UTES."""
    purpose = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, purpose=None, **kwargs):

        super().__init__(**kwargs)

        if purpose is not None:
            self.purpose = purpose


@abstract
class EnergyService(Service):
    """Abstract class to represent logical entities in the energy system, e.g. demand response services, energy markets, etc."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractBuilding(Asset):
    """Describes the shared properties of building, building unit and aggregated building"""
    energyLabel = EAttribute(eType=EnergyLabelEnum, derived=False, changeable=True)
    energyIndex = EAttribute(eType=EDouble, derived=False, changeable=True)
    asset = EReference(ordered=True, unique=True, containment=True, upper=-1)
    buildingUsage = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, energyLabel=None, asset=None, energyIndex=None, buildingUsage=None, **kwargs):

        super().__init__(**kwargs)

        if energyLabel is not None:
            self.energyLabel = energyLabel

        if energyIndex is not None:
            self.energyIndex = energyIndex

        if asset:
            self.asset.extend(asset)

        if buildingUsage is not None:
            self.buildingUsage = buildingUsage


class WindPotential(Potential):
    """Represents wind potential"""
    value = EAttribute(eType=EDouble, derived=False, changeable=True)
    height = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, value=None, height=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value

        if height is not None:
            self.height = height


class DateTimeProfile(StaticProfile):
    """Describes a profile using one or more Profile elements. Each element defines a from- and a to-datetime and a value which is valid for this range. The to-field may be ommitted, meaning this value is valid for all time after the to-date."""
    element = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, element=None, **kwargs):

        super().__init__(**kwargs)

        if element:
            self.element.extend(element)


class SingleValue(StaticProfile):
    """A profile used to define a single value. This should be used when no information is present about the time. E.g. the price of a PV panel as currently known
When a model queries for a value from a certain date (and to a certain date), that information will be ignored and it will always return this value."""
    value = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class StringLabelDistribution(LabelDistribution):
    """Defines a distribution in terms of self-defined labels"""
    stringPerc = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, stringPerc=None, **kwargs):

        super().__init__(**kwargs)

        if stringPerc:
            self.stringPerc.extend(stringPerc)


class EnergyLabelDistribution(LabelDistribution):
    """Defines a distribution in terms of energy labels"""
    labelPerc = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, labelPerc=None, **kwargs):

        super().__init__(**kwargs)

        if labelPerc:
            self.labelPerc.extend(labelPerc)


class FromToDistribution(LabelDistribution):
    """Defines a distribution in terms of 'from' and 'to'"""
    fromToPerc = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, fromToPerc=None, **kwargs):

        super().__init__(**kwargs)

        if fromToPerc:
            self.fromToPerc.extend(fromToPerc)


class URIProfile(ExternalProfile):
    """Describes a reference to a profile in an information system using a URI (e.g. a URI to a profile in Energy Information System (EIS))"""
    URI = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, URI=None, **kwargs):

        super().__init__(**kwargs)

        if URI is not None:
            self.URI = URI


@abstract
class DatabaseProfile(ExternalProfile):
    """Describes the fields of a generic database-based profile"""
    host = EAttribute(eType=EString, derived=False, changeable=True)
    port = EAttribute(eType=EInt, derived=False, changeable=True)
    database = EAttribute(eType=EString, derived=False, changeable=True)
    filters = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, host=None, port=None, database=None, filters=None, **kwargs):

        super().__init__(**kwargs)

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        if database is not None:
            self.database = database

        if filters is not None:
            self.filters = filters


class GasCommodity(Commodity):
    """Defines a gas commodity. This class can be used as an abstract way of modelling gas commodity and can be used in conjunction with electricity commodity and heat commodity. If more detailed modelling is necessary, use energy carriers."""
    pressure = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, pressure=None, **kwargs):

        super().__init__(**kwargs)

        if pressure is not None:
            self.pressure = pressure


class HeatCommodity(Commodity):
    """Defines a heat commodity"""
    supplyTemperature = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    returnTemperature = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, supplyTemperature=None, returnTemperature=None, **kwargs):

        super().__init__(**kwargs)

        if supplyTemperature is not None:
            self.supplyTemperature = supplyTemperature

        if returnTemperature is not None:
            self.returnTemperature = returnTemperature


class ElectricityCommodity(Commodity):
    """Defines a electricity commodity"""
    voltage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, voltage=None, **kwargs):

        super().__init__(**kwargs)

        if voltage is not None:
            self.voltage = voltage


class Range(StaticProfile):
    """Defines a range between two values"""
    minValue = EAttribute(eType=EDouble, derived=False, changeable=True)
    maxValue = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, minValue=None, maxValue=None, **kwargs):

        super().__init__(**kwargs)

        if minValue is not None:
            self.minValue = minValue

        if maxValue is not None:
            self.maxValue = maxValue


class SolarPotential(Potential):
    """Defines the potential for solar energy"""
    value = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    SolarPotentialType = EAttribute(eType=PVInstallationTypeEnum, derived=False, changeable=True)
    fullLoadHours = EAttribute(eType=EInt, derived=False, changeable=True)
    area = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, value=None, SolarPotentialType=None, fullLoadHours=None, area=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value

        if SolarPotentialType is not None:
            self.SolarPotentialType = SolarPotentialType

        if fullLoadHours is not None:
            self.fullLoadHours = fullLoadHours

        if area is not None:
            self.area = area


class ProfileReference(StaticProfile):
    """Used to refer to profiles defined in the Energy System Information section"""
    multiplier = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=1.0)
    reference = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, multiplier=None, reference=None, **kwargs):

        super().__init__(**kwargs)

        if multiplier is not None:
            self.multiplier = multiplier

        if reference is not None:
            self.reference = reference


class ResidualHeatSourcePotential(Potential):
    """Defines the residual heat potential in a specific area."""
    value = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    type = EAttribute(eType=ResidualHeatSourceTypeEnum, derived=False, changeable=True)
    associatedConversionAsset = EReference(ordered=True, unique=True, containment=False)
    residualHeatSource = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, value=None, type=None, associatedConversionAsset=None, residualHeatSource=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value

        if type is not None:
            self.type = type

        if associatedConversionAsset is not None:
            self.associatedConversionAsset = associatedConversionAsset

        if residualHeatSource is not None:
            self.residualHeatSource = residualHeatSource


class EnergyCommodity(Commodity):
    """Generic energy commodity, to be used in (national) energy balances"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractGTPotential(Potential):
    """Abstract class to describe geothermal potential"""
    geothermalSource = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, geothermalSource=None, **kwargs):

        super().__init__(**kwargs)

        if geothermalSource:
            self.geothermalSource.extend(geothermalSource)


class UTESPotential(Potential):
    """Defines the potential for underground thermal energy storage (UTES). E.g. ATES or BTES potential"""
    value = EAttribute(eType=EDouble, derived=False, changeable=True)
    type = EAttribute(eType=UTESPotentialTypeEnum, derived=False, changeable=True)
    UTES = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, value=None, type=None, UTES=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value

        if type is not None:
            self.type = type

        if UTES:
            self.UTES.extend(UTES)


class BiomassPotential(Potential):

    value = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)

    def __init__(self, *, value=None, **kwargs):

        super().__init__(**kwargs)

        if value is not None:
            self.value = value


class Glass(Asset):

    uWindow = EAttribute(eType=EDouble, derived=False, changeable=True)
    glasType = EAttribute(eType=GlassTypeEnum, derived=False, changeable=True,
                          default_value=GlassTypeEnum.UNDEFINED)

    def __init__(self, *, uWindow=None, glasType=None, **kwargs):

        super().__init__(**kwargs)

        if uWindow is not None:
            self.uWindow = uWindow

        if glasType is not None:
            self.glasType = glasType


class SearchAreaWind(Potential):

    fullLoadHours = EAttribute(eType=EInt, derived=False, changeable=True)
    area = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, fullLoadHours=None, area=None, **kwargs):

        super().__init__(**kwargs)

        if fullLoadHours is not None:
            self.fullLoadHours = fullLoadHours

        if area is not None:
            self.area = area


class SearchAreaSolar(Potential):

    fullLoadHours = EAttribute(eType=EInt, derived=False, changeable=True)
    area = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, fullLoadHours=None, area=None, **kwargs):

        super().__init__(**kwargs)

        if fullLoadHours is not None:
            self.fullLoadHours = fullLoadHours

        if area is not None:
            self.area = area


class BuildingTypeDistribution(LabelDistribution):

    buildingTypePercentage = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, buildingTypePercentage=None, **kwargs):

        super().__init__(**kwargs)

        if buildingTypePercentage:
            self.buildingTypePercentage.extend(buildingTypePercentage)


class ResidentialBuildingTypeDistribution(LabelDistribution):

    residentialBuildingTypePercentage = EReference(
        ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, residentialBuildingTypePercentage=None, **kwargs):

        super().__init__(**kwargs)

        if residentialBuildingTypePercentage:
            self.residentialBuildingTypePercentage.extend(residentialBuildingTypePercentage)


class HousingTypeDistribution(LabelDistribution):

    housingTypePercentage = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, housingTypePercentage=None, **kwargs):

        super().__init__(**kwargs)

        if housingTypePercentage:
            self.housingTypePercentage.extend(housingTypePercentage)


@abstract
class Producer(EnergyAsset):
    """An abstract class that describes EnergyAssets that can produce energy. It is one of the 5 capabilities in ESDL"""
    prodType = EAttribute(eType=RenewableTypeEnum, derived=False,
                          changeable=True, default_value=RenewableTypeEnum.RENEWABLE)
    operationalHours = EAttribute(eType=EInt, derived=False, changeable=True)
    fullLoadHours = EAttribute(eType=EInt, derived=False, changeable=True)
    power = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, prodType=None, operationalHours=None, fullLoadHours=None, power=None, **kwargs):

        super().__init__(**kwargs)

        if prodType is not None:
            self.prodType = prodType

        if operationalHours is not None:
            self.operationalHours = operationalHours

        if fullLoadHours is not None:
            self.fullLoadHours = fullLoadHours

        if power is not None:
            self.power = power


@abstract
class Consumer(EnergyAsset):
    """An abstract class that describes EnergyAssets that can consume energy. It is one of the 5 capabilities in ESDL"""
    consType = EAttribute(eType=ConsTypeEnum, derived=False, changeable=True,
                          default_value=ConsTypeEnum.PRIMARY)
    power = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, consType=None, power=None, **kwargs):

        super().__init__(**kwargs)

        if consType is not None:
            self.consType = consType

        if power is not None:
            self.power = power


@abstract
class Storage(EnergyAsset):
    """An abstract class that describes EnergyAssets that can store energy. It is one of the 5 capabilities in ESDL"""
    capacity = EAttribute(eType=EDouble, derived=False, changeable=True)
    chargeEfficiency = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    dischargeEfficiency = EAttribute(eType=EDouble, derived=False,
                                     changeable=True, default_value=0.0)
    selfDischargeRate = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    fillLevel = EAttribute(eType=EDouble, derived=False, changeable=True)
    maxChargeRate = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    maxDischargeRate = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    profile = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, capacity=None, chargeEfficiency=None, profile=None, dischargeEfficiency=None, selfDischargeRate=None, fillLevel=None, maxChargeRate=None, maxDischargeRate=None, **kwargs):

        super().__init__(**kwargs)

        if capacity is not None:
            self.capacity = capacity

        if chargeEfficiency is not None:
            self.chargeEfficiency = chargeEfficiency

        if dischargeEfficiency is not None:
            self.dischargeEfficiency = dischargeEfficiency

        if selfDischargeRate is not None:
            self.selfDischargeRate = selfDischargeRate

        if fillLevel is not None:
            self.fillLevel = fillLevel

        if maxChargeRate is not None:
            self.maxChargeRate = maxChargeRate

        if maxDischargeRate is not None:
            self.maxDischargeRate = maxDischargeRate

        if profile is not None:
            self.profile = profile


@abstract
class Conversion(EnergyAsset):
    """An abstract class that describes EnergyAssets that can convert one energy carrier into another. It is one of the 5 capabilities in ESDL"""
    efficiency = EAttribute(eType=EDouble, derived=False, changeable=True)
    operationalHours = EAttribute(eType=EInt, derived=False, changeable=True)
    fullLoadHours = EAttribute(eType=EInt, derived=False, changeable=True)
    power = EAttribute(eType=EDouble, derived=False, changeable=True)
    residualHeatSourcePotential = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, efficiency=None, operationalHours=None, fullLoadHours=None, power=None, residualHeatSourcePotential=None, **kwargs):

        super().__init__(**kwargs)

        if efficiency is not None:
            self.efficiency = efficiency

        if operationalHours is not None:
            self.operationalHours = operationalHours

        if fullLoadHours is not None:
            self.fullLoadHours = fullLoadHours

        if power is not None:
            self.power = power

        if residualHeatSourcePotential is not None:
            self.residualHeatSourcePotential = residualHeatSourcePotential


@abstract
class Transport(EnergyAsset):
    """An abstract class that describes EnergyAssets that can transport energy. It is one of the 5 capabilities in ESDL"""
    capacity = EAttribute(eType=EDouble, derived=False, changeable=True)
    efficiency = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, capacity=None, efficiency=None, **kwargs):

        super().__init__(**kwargs)

        if capacity is not None:
            self.capacity = capacity

        if efficiency is not None:
            self.efficiency = efficiency


class BuildingUnit(AbstractBuilding):
    """Describes a physical part of a building. In dutch 'verblijfsobject' in the BAG national building and address registry. This can be used e.g. to model appartments in appartment complexes"""
    type = EAttribute(eType=BuildingTypeEnum, derived=False, changeable=True)
    housingType = EAttribute(eType=HousingTypeEnum, derived=False, changeable=True)
    numberOfInhabitants = EAttribute(eType=EInt, derived=False, changeable=True)
    inhabitantsType = EAttribute(eType=InhabitantsTypeEnum, derived=False, changeable=True)
    floorArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    numberOfFloors = EAttribute(eType=EInt, derived=False, changeable=True)
    slantedRoofArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    flatRoofArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    roofType = EAttribute(eType=RoofTypeEnum, derived=False, changeable=True)
    wallArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    windowArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    rcFloor = EAttribute(eType=EDouble, derived=False, changeable=True)
    rcWall = EAttribute(eType=EDouble, derived=False, changeable=True)
    rfRoof = EAttribute(eType=EDouble, derived=False, changeable=True)
    uWindow = EAttribute(eType=EDouble, derived=False, changeable=True)
    glassType = EAttribute(eType=GlassTypeEnum, derived=False,
                           changeable=True, default_value=GlassTypeEnum.UNDEFINED)
    ventilationType = EAttribute(eType=VentilationTypeEnum, derived=False,
                                 changeable=True, default_value=VentilationTypeEnum.UNDEFINED)

    def __init__(self, *, type=None, housingType=None, numberOfInhabitants=None, inhabitantsType=None, floorArea=None, numberOfFloors=None, slantedRoofArea=None, flatRoofArea=None, roofType=None, wallArea=None, windowArea=None, rcFloor=None, rcWall=None, rfRoof=None, uWindow=None, glassType=None, ventilationType=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if housingType is not None:
            self.housingType = housingType

        if numberOfInhabitants is not None:
            self.numberOfInhabitants = numberOfInhabitants

        if inhabitantsType is not None:
            self.inhabitantsType = inhabitantsType

        if floorArea is not None:
            self.floorArea = floorArea

        if numberOfFloors is not None:
            self.numberOfFloors = numberOfFloors

        if slantedRoofArea is not None:
            self.slantedRoofArea = slantedRoofArea

        if flatRoofArea is not None:
            self.flatRoofArea = flatRoofArea

        if roofType is not None:
            self.roofType = roofType

        if wallArea is not None:
            self.wallArea = wallArea

        if windowArea is not None:
            self.windowArea = windowArea

        if rcFloor is not None:
            self.rcFloor = rcFloor

        if rcWall is not None:
            self.rcWall = rcWall

        if rfRoof is not None:
            self.rfRoof = rfRoof

        if uWindow is not None:
            self.uWindow = uWindow

        if glassType is not None:
            self.glassType = glassType

        if ventilationType is not None:
            self.ventilationType = ventilationType


class Building(AbstractBuilding):
    """Represents a physical building"""
    buildingYear = EAttribute(eType=EInt, derived=False, changeable=True)
    residentialBuildingType = EAttribute(
        eType=ResidentialBuildingTypeEnum, derived=False, changeable=True)
    floorArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    numberOfFloors = EAttribute(eType=EInt, derived=False, changeable=True)
    slantedRoofArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    flatRoofArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    roofType = EAttribute(eType=RoofTypeEnum, derived=False, changeable=True)
    wallArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    windowArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    perimeter = EAttribute(eType=EDouble, derived=False, changeable=True)
    height = EAttribute(eType=EDouble, derived=False, changeable=True)
    rcFloor = EAttribute(eType=EDouble, derived=False, changeable=True)
    rcWall = EAttribute(eType=EDouble, derived=False, changeable=True)
    rcRoof = EAttribute(eType=EDouble, derived=False, changeable=True)
    uWindow = EAttribute(eType=EDouble, derived=False, changeable=True)
    orientation = EAttribute(eType=EInt, derived=False, changeable=True)
    glassType = EAttribute(eType=GlassTypeEnum, derived=False, changeable=True)
    ventilationType = EAttribute(eType=VentilationTypeEnum, derived=False, changeable=True)

    def __init__(self, *, buildingYear=None, residentialBuildingType=None, floorArea=None, numberOfFloors=None, slantedRoofArea=None, flatRoofArea=None, roofType=None, wallArea=None, windowArea=None, perimeter=None, height=None, rcFloor=None, rcWall=None, rcRoof=None, uWindow=None, orientation=None, glassType=None, ventilationType=None, **kwargs):

        super().__init__(**kwargs)

        if buildingYear is not None:
            self.buildingYear = buildingYear

        if residentialBuildingType is not None:
            self.residentialBuildingType = residentialBuildingType

        if floorArea is not None:
            self.floorArea = floorArea

        if numberOfFloors is not None:
            self.numberOfFloors = numberOfFloors

        if slantedRoofArea is not None:
            self.slantedRoofArea = slantedRoofArea

        if flatRoofArea is not None:
            self.flatRoofArea = flatRoofArea

        if roofType is not None:
            self.roofType = roofType

        if wallArea is not None:
            self.wallArea = wallArea

        if windowArea is not None:
            self.windowArea = windowArea

        if perimeter is not None:
            self.perimeter = perimeter

        if height is not None:
            self.height = height

        if rcFloor is not None:
            self.rcFloor = rcFloor

        if rcWall is not None:
            self.rcWall = rcWall

        if rcRoof is not None:
            self.rcRoof = rcRoof

        if uWindow is not None:
            self.uWindow = uWindow

        if orientation is not None:
            self.orientation = orientation

        if glassType is not None:
            self.glassType = glassType

        if ventilationType is not None:
            self.ventilationType = ventilationType


class GeothermalPotential(AbstractGTPotential):
    """Defines the geothermal potential in a specific area. This type focusses on temperature and depth of the well. See GeothermalEnergyPotental for class focussing on Energy"""
    temperature = EAttribute(eType=EInt, derived=False, changeable=True)
    depth = EAttribute(eType=EInt, derived=False, changeable=True)
    potential = EAttribute(eType=GeothermalPotentialEnum, derived=False, changeable=True)
    powerPerDoublet = EAttribute(eType=GeothermalPowerEnum, derived=False,
                                 changeable=True, default_value=GeothermalPowerEnum.UNKNOWN)

    def __init__(self, *, temperature=None, depth=None, potential=None, powerPerDoublet=None, **kwargs):

        super().__init__(**kwargs)

        if temperature is not None:
            self.temperature = temperature

        if depth is not None:
            self.depth = depth

        if potential is not None:
            self.potential = potential

        if powerPerDoublet is not None:
            self.powerPerDoublet = powerPerDoublet


class DemandResponseService(EnergyService):
    """Indicates a service supporting demand response in the energy system"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class AggregatorService(EnergyService):
    """Indicates a aggregator service exploiting flexibility in the energy system"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class AggregatedBuilding(AbstractBuilding):
    """Represents more than one building aggregated into one entity. It supports different types of aggregation, such as building type, energy label etc."""
    numberOfBuildings = EAttribute(eType=EInt, derived=False, changeable=True)
    floorArea = EAttribute(eType=EDouble, derived=False, changeable=True)
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)
    energyLabelDistribution = EReference(ordered=True, unique=True, containment=True)
    buildingYearDistribution = EReference(ordered=True, unique=True, containment=True)
    buildingTypeDistribution = EReference(ordered=True, unique=True, containment=True)
    residentialBuildingTypeDistribution = EReference(ordered=True, unique=True, containment=True)
    housingTypeDistribution = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, aggregationOf=None, numberOfBuildings=None, energyLabelDistribution=None, buildingYearDistribution=None, buildingTypeDistribution=None, residentialBuildingTypeDistribution=None, housingTypeDistribution=None, floorArea=None, **kwargs):

        super().__init__(**kwargs)

        if numberOfBuildings is not None:
            self.numberOfBuildings = numberOfBuildings

        if floorArea is not None:
            self.floorArea = floorArea

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)

        if energyLabelDistribution is not None:
            self.energyLabelDistribution = energyLabelDistribution

        if buildingYearDistribution is not None:
            self.buildingYearDistribution = buildingYearDistribution

        if buildingTypeDistribution is not None:
            self.buildingTypeDistribution = buildingTypeDistribution

        if residentialBuildingTypeDistribution is not None:
            self.residentialBuildingTypeDistribution = residentialBuildingTypeDistribution

        if housingTypeDistribution is not None:
            self.housingTypeDistribution = housingTypeDistribution


class InfluxDBProfile(DatabaseProfile):
    """Describes a profile based on a measurement and field as part of an InfluxDB timeseries query"""
    measurement = EAttribute(eType=EString, derived=False, changeable=True)
    field = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, measurement=None, field=None, **kwargs):

        super().__init__(**kwargs)

        if measurement is not None:
            self.measurement = measurement

        if field is not None:
            self.field = field


@abstract
class ControlStrategy(EnergyService):
    """Defines a control strategy for a specific asset"""
    energyAsset = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, energyAsset=None, **kwargs):

        super().__init__(**kwargs)

        if energyAsset is not None:
            self.energyAsset = energyAsset


class EnergyMarket(EnergyService):
    """Defines an EnergyMarket of the energy system. A market is defined by specifying the assets that participate in this market."""
    asset = EReference(ordered=True, unique=True, containment=False, upper=-1)
    carrier = EReference(ordered=True, unique=True, containment=False)
    parameters = EReference(ordered=True, unique=True, containment=True, upper=-1)

    def __init__(self, *, asset=None, carrier=None, parameters=None, **kwargs):

        super().__init__(**kwargs)

        if asset:
            self.asset.extend(asset)

        if carrier is not None:
            self.carrier = carrier

        if parameters:
            self.parameters.extend(parameters)


class GeothermalEnergyPotential(AbstractGTPotential):
    """Defines the geothermal potential in a specific area. This type focusses on energy and depth of the well. See GeothermalPotental for class focussing on temperature"""
    depth = EAttribute(eType=EInt, derived=False, changeable=True)
    value = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)

    def __init__(self, *, depth=None, value=None, **kwargs):

        super().__init__(**kwargs)

        if depth is not None:
            self.depth = depth

        if value is not None:
            self.value = value


class WindTurbine(Producer):
    """Describes an individual wind turbine. A wind turbine is a producer capability"""
    rotorDiameter = EAttribute(eType=EDouble, derived=False, changeable=True)
    height = EAttribute(eType=EDouble, derived=False, changeable=True)
    type = EAttribute(eType=WindTurbineTypeEnum, derived=False, changeable=True)

    def __init__(self, *, rotorDiameter=None, height=None, type=None, **kwargs):

        super().__init__(**kwargs)

        if rotorDiameter is not None:
            self.rotorDiameter = rotorDiameter

        if height is not None:
            self.height = height

        if type is not None:
            self.type = type


class PVPanel(Producer):
    """Describes an individual PV panel. See PVInstallation for multiple PV panels. This is a Producer capability"""
    panelEfficiency = EAttribute(eType=EDouble, derived=False, changeable=True)
    inverterEfficiency = EAttribute(eType=EDouble, derived=False, changeable=True)
    angle = EAttribute(eType=EInt, derived=False, changeable=True)
    orientation = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, panelEfficiency=None, inverterEfficiency=None, angle=None, orientation=None, **kwargs):

        super().__init__(**kwargs)

        if panelEfficiency is not None:
            self.panelEfficiency = panelEfficiency

        if inverterEfficiency is not None:
            self.inverterEfficiency = inverterEfficiency

        if angle is not None:
            self.angle = angle

        if orientation is not None:
            self.orientation = orientation


class Battery(Storage):
    """A battery can store electrical energy. This is a Storage capability"""
    maxChargeDischargeCycles = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, maxChargeDischargeCycles=None, **kwargs):

        super().__init__(**kwargs)

        if maxChargeDischargeCycles is not None:
            self.maxChargeDischargeCycles = maxChargeDischargeCycles


class AggregatedConsumer(Consumer):
    """Represents an aggregation of multiple consumers as one aggregated consumer. It allows you to reference the consumers it is aggregated of by using the aggregationOf reference. Can be used to aggregate a heterogeneous collection of consumers (e.g. of different types)"""
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, aggregationOf=None, **kwargs):

        super().__init__(**kwargs)

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)


class AggregatedProducer(Producer):
    """Represents an aggregation of multiple producers as one aggregated producer. It allows you to reference the producers it is aggregated of by using the aggregationOf reference. Can be used to aggregate a heterogeneous collection of producers (e.g. of different types)"""
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, aggregationOf=None, **kwargs):

        super().__init__(**kwargs)

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)


class GenericConsumer(Consumer):
    """Generic consumer class that can be used in cases that the actual asset type is not important or not supported yet in ESDL"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GenericProducer(Producer):
    """Generic producer class that can be used in cases that the actual asset type is not important or not supported yet in ESDL"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GenericStorage(Storage):
    """Generic storage class that can be used in cases that the actual asset type is not important or not supported yet in ESDL"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GenericTransport(Transport):
    """Generic transport class that can be used in cases that the actual asset type is not important or not supported yet in ESDL"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GenericConversion(Conversion):
    """Generic conversion class that can be used in cases that the actual asset type is not important or not supported yet in ESDL"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class AggregatedTransport(Transport):
    """Represents an aggregation of multiple transport assets as one aggregated transport asset. It allows you to reference the transport asset it is aggregated of by using the aggregationOf reference. Can be used to aggregate a heterogeneous collection of transport assets (e.g. of different types)"""
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, aggregationOf=None, **kwargs):

        super().__init__(**kwargs)

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)


class AggregatedConversion(Conversion):
    """Represents an aggregation of multiple conversion assets as one aggregated conversion asset. It allows you to reference the conversion asset it is aggregated of by using the aggregationOf reference. Can be used to aggregate a heterogeneous collection of conversion assets (e.g. of different types)"""
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, aggregationOf=None, **kwargs):

        super().__init__(**kwargs)

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)


class AggregatedStorage(Storage):
    """Represents an aggregation of multiple storage assets as one aggregated storage asset. It allows you to reference the storage asset it is aggregated of by using the aggregationOf reference. Can be used to aggregate a heterogeneous collection of storage assets (e.g. of different types)"""
    aggregationOf = EReference(ordered=True, unique=True, containment=False, upper=-1)

    def __init__(self, *, aggregationOf=None, **kwargs):

        super().__init__(**kwargs)

        if aggregationOf:
            self.aggregationOf.extend(aggregationOf)


class HeatStorage(Storage):
    """Generic heat storage asset with min and max temperatures"""
    minStorageTemperature = EAttribute(eType=EDouble, derived=False, changeable=True)
    maxStorageTemperature = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, minStorageTemperature=None, maxStorageTemperature=None, **kwargs):

        super().__init__(**kwargs)

        if minStorageTemperature is not None:
            self.minStorageTemperature = minStorageTemperature

        if maxStorageTemperature is not None:
            self.maxStorageTemperature = maxStorageTemperature


class GasHeater(Conversion):
    """Converts gas to heat, e.g. a gas boiler or gas heater"""
    minimumBurnRate = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    type = EAttribute(eType=GasHeaterTypeEnum, derived=False, changeable=True)

    def __init__(self, *, minimumBurnRate=None, type=None, **kwargs):

        super().__init__(**kwargs)

        if minimumBurnRate is not None:
            self.minimumBurnRate = minimumBurnRate

        if type is not None:
            self.type = type


class SourceProducer(Producer):
    """Represents a generic source that produces a certain commodity. Used to model the rest of the energy system that is out of the current scope"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class SinkConsumer(Consumer):
    """Represents a generic sink that consumes a certain commodity. Used to model the rest of the energy system that is out of the current scope"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GeothermalSource(Producer):
    """Geothermal source including the installation that connects the source to the network"""
    wellDepth = EAttribute(eType=EDouble, derived=False, changeable=True)
    geothermalSourceType = EAttribute(eType=GeothermalSourceTypeEnum,
                                      derived=False, changeable=True)
    COP = EAttribute(eType=EDouble, derived=False, changeable=True)
    aquiferTemperature = EAttribute(eType=EDouble, derived=False, changeable=True)
    flowRate = EAttribute(eType=EDouble, derived=False, changeable=True)
    pumpPower = EAttribute(eType=EDouble, derived=False, changeable=True)
    geothermalPotential = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, wellDepth=None, geothermalSourceType=None, COP=None, aquiferTemperature=None, flowRate=None, pumpPower=None, geothermalPotential=None, **kwargs):

        super().__init__(**kwargs)

        if wellDepth is not None:
            self.wellDepth = wellDepth

        if geothermalSourceType is not None:
            self.geothermalSourceType = geothermalSourceType

        if COP is not None:
            self.COP = COP

        if aquiferTemperature is not None:
            self.aquiferTemperature = aquiferTemperature

        if flowRate is not None:
            self.flowRate = flowRate

        if pumpPower is not None:
            self.pumpPower = pumpPower

        if geothermalPotential is not None:
            self.geothermalPotential = geothermalPotential


@abstract
class CoGeneration(Conversion):
    """Abstract asset describing a co-generation plant that produces heat and electricity"""
    heatEfficiency = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    electricalEfficiency = EAttribute(eType=EDouble, derived=False,
                                      changeable=True, default_value=0.0)
    HERatio = EAttribute(eType=EDouble, derived=False, changeable=True)
    fuelType = EAttribute(eType=PowerPlantFuelEnum, derived=False, changeable=True)
    leadCommodity = EAttribute(eType=CommodityEnum, derived=False, changeable=True)
    energyCarrier = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, heatEfficiency=None, electricalEfficiency=None, energyCarrier=None, HERatio=None, fuelType=None, leadCommodity=None, **kwargs):

        super().__init__(**kwargs)

        if heatEfficiency is not None:
            self.heatEfficiency = heatEfficiency

        if electricalEfficiency is not None:
            self.electricalEfficiency = electricalEfficiency

        if HERatio is not None:
            self.HERatio = HERatio

        if fuelType is not None:
            self.fuelType = fuelType

        if leadCommodity is not None:
            self.leadCommodity = leadCommodity

        if energyCarrier is not None:
            self.energyCarrier = energyCarrier


class HeatPump(Conversion):
    """Describes a Heat Pump"""
    source = EAttribute(eType=SourceTypeEnum, derived=False, changeable=True)
    stages = EAttribute(eType=EInt, derived=False, changeable=True, default_value=1)
    COP = EAttribute(eType=EDouble, derived=False, changeable=True)
    additionalHeatingSourceType = EAttribute(
        eType=AdditionalHeatingSourceTypeEnum, derived=False, changeable=True)

    def __init__(self, *, source=None, stages=None, COP=None, additionalHeatingSourceType=None, **kwargs):

        super().__init__(**kwargs)

        if source is not None:
            self.source = source

        if stages is not None:
            self.stages = stages

        if COP is not None:
            self.COP = COP

        if additionalHeatingSourceType is not None:
            self.additionalHeatingSourceType = additionalHeatingSourceType


class HeatingDemand(Consumer):
    """Describes the heating demand of e.g. a household, area, etc."""
    type = EAttribute(eType=HeatDemandTypeEnum, derived=False, changeable=True)
    deviceType = EAttribute(eType=HeatRadiationDeviceTypeEnum, derived=False, changeable=True)

    def __init__(self, *, type=None, deviceType=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if deviceType is not None:
            self.deviceType = deviceType


class ElectricityDemand(Consumer):
    """Describes the electricity demand of e.g. a household, area, etc."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GasDemand(Consumer):
    """Describes the gas demand of e.g. a household, area, etc. This can be used for all types of gasses (e.g. CO2, Natural Gas, Hydrogen, etc.)"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PowerPlant(Conversion):
    """Defines an electricity generating plant"""
    fuel = EAttribute(eType=PowerPlantFuelEnum, derived=False, changeable=True)
    maxLoad = EAttribute(eType=EInt, derived=False, changeable=True)
    minLoad = EAttribute(eType=EInt, derived=False, changeable=True)
    effMaxLoad = EAttribute(eType=EDouble, derived=False, changeable=True)
    effMinLoad = EAttribute(eType=EDouble, derived=False, changeable=True)
    energyCarrier = EReference(ordered=True, unique=True, containment=False)
    mustRun = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, fuel=None, maxLoad=None, minLoad=None, effMaxLoad=None, effMinLoad=None, energyCarrier=None, mustRun=None, **kwargs):

        super().__init__(**kwargs)

        if fuel is not None:
            self.fuel = fuel

        if maxLoad is not None:
            self.maxLoad = maxLoad

        if minLoad is not None:
            self.minLoad = minLoad

        if effMaxLoad is not None:
            self.effMaxLoad = effMaxLoad

        if effMinLoad is not None:
            self.effMinLoad = effMinLoad

        if energyCarrier is not None:
            self.energyCarrier = energyCarrier

        if mustRun is not None:
            self.mustRun = mustRun


class EVChargingStation(Consumer):
    """Represents a charging station for electrical vehicles. Both single private-owned car chargers and public charging spaces can be modelled by this class"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Losses(Consumer):
    """Used to define losses explicitly (as a Consumer capability)"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PowerToX(Conversion):
    """Represents the ability to convert electricity to some other form of energy"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class CCS(Storage):
    """Represents Carbon Capture and Storage"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class XToPower(Conversion):
    """Represents the ability to convert some other form of energy to electricity"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class CoolingDemand(Consumer):
    """Describes the cooling demand of e.g. a building"""
    deviceType = EAttribute(eType=CoolingDeviceType, derived=False, changeable=True)

    def __init__(self, *, deviceType=None, **kwargs):

        super().__init__(**kwargs)

        if deviceType is not None:
            self.deviceType = deviceType


class Airco(Conversion):
    """Represents an air conditioning unit"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class EnergyDemand(Consumer):
    """Allows to describe the total energy demand when differentiation between energy carriers is not possible or required, otherwise e.g. ElectricityDemand or HeatingDemand is an alternative"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class SolarCollector(Producer):
    """Defines a SolarCollector asset"""
    type = EAttribute(eType=SolarCollectorTypeEnum, derived=False, changeable=True)

    def __init__(self, *, type=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type


class ResidualHeatSource(Producer):
    """Defines a source of residual heat, e.g. a data center or factory"""
    type = EAttribute(eType=ResidualHeatSourceTypeEnum, derived=False, changeable=True)
    residualHeatSourcePotential = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, type=None, residualHeatSourcePotential=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if residualHeatSourcePotential is not None:
            self.residualHeatSourcePotential = residualHeatSourcePotential


class FermentationPlant(Conversion):
    """Defines a plant fuelled by biomass"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class MobilityDemand(Consumer):
    """Energy demand of the mobility sector. Allows to specify the vehicle types, fuel types and their efficiency and distance travelled"""
    type = EAttribute(eType=VehicleTypeEnum, derived=False, changeable=True, upper=-1)
    fuelType = EAttribute(eType=MobilityFuelTypeEnum, derived=False, changeable=True)
    distance = EAttribute(eType=EInt, derived=False, changeable=True)
    efficiency = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, type=None, fuelType=None, distance=None, efficiency=None, **kwargs):

        super().__init__(**kwargs)

        if type:
            self.type.extend(type)

        if fuelType is not None:
            self.fuelType = fuelType

        if distance is not None:
            self.distance = distance

        if efficiency is not None:
            self.efficiency = efficiency


class GasStorage(Storage):
    """Defines a gas storage asset, see also CCS"""
    minStoragePressure = EAttribute(eType=EDouble, derived=False, changeable=True)
    maxStoragePressure = EAttribute(eType=EDouble, derived=False,
                                    changeable=True, default_value=0.0)

    def __init__(self, *, minStoragePressure=None, maxStoragePressure=None, **kwargs):

        super().__init__(**kwargs)

        if minStoragePressure is not None:
            self.minStoragePressure = minStoragePressure

        if maxStoragePressure is not None:
            self.maxStoragePressure = maxStoragePressure


class DrivenByDemand(ControlStrategy):
    """Control strategy specifying that an asset is driven by the demand of one of the output ports"""
    outPort = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, outPort=None, **kwargs):

        super().__init__(**kwargs)

        if outPort is not None:
            self.outPort = outPort


class GasConversion(Conversion):
    """Defines an asset that can convert gas into another form of gas. E.g. SMR or ATR."""
    type = EAttribute(eType=GasConversionTypeEnum, derived=False, changeable=True)
    outputPressure = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, type=None, outputPressure=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if outputPressure is not None:
            self.outputPressure = outputPressure


class DrivenBySupply(ControlStrategy):
    """Control strategy specifying that an asset is driven by the supply of one of the input ports (used in ESDL-based simulation tools)"""
    inPort = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, inPort=None, **kwargs):

        super().__init__(**kwargs)

        if inPort is not None:
            self.inPort = inPort


class DrivenByProfile(ControlStrategy):
    """Control strategy specifying that an asset is driven by a profile specified in one of the ports (used in ESDL-based simulation tools)"""
    profile = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, profile=None, **kwargs):

        super().__init__(**kwargs)

        if profile is not None:
            self.profile = profile


class WaterToPower(Producer):
    """Defines an asset that uses water to produce electricity. E.g.  hydro power, tidal power, wave power or osmotic power"""
    type = EAttribute(eType=WaterToPowerTypeEnum, derived=False, changeable=True)

    def __init__(self, *, type=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type


class EnergyNetwork(Transport):
    """Defines an energy network. Used for national energy balances, when the specific energy carrier is not required"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractConductor(Transport):
    """Abstract class to describe conductors such as cables and pipes and joining them using a joint"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractSwitch(Transport):
    """Abstract class to describe switches such as valve and a circuit breaker"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractTransformer(Transport):
    """Abstract class to describe transformers, such as Heat exchangers, transformers and pumps"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


@abstract
class AbstractConnection(Transport):
    """Abstract class to describe connections of a building to a grid. E.g. a heat connection, gas connection and electricity connection"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class RoomHeater(Conversion):
    """Defines an asset for heating rooms, such as infra red panels, gas stove, etc."""
    type = EAttribute(eType=RoomHeaterTypeEnum, derived=False, changeable=True)

    def __init__(self, *, type=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type


class BiomassHeater(Conversion):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class StorageStrategy(ControlStrategy):
    """Control strategy specifying that a storage asset is driven by two profiles specifying the marginal cost to define its charging and discharging behavior (used in ESDL-based simulation tools)"""
    marginalChargeCosts = EReference(ordered=True, unique=True, containment=True)
    marginalDischargeCosts = EReference(ordered=True, unique=True, containment=True)

    def __init__(self, *, marginalChargeCosts=None, marginalDischargeCosts=None, **kwargs):

        super().__init__(**kwargs)

        if marginalChargeCosts is not None:
            self.marginalChargeCosts = marginalChargeCosts

        if marginalDischargeCosts is not None:
            self.marginalDischargeCosts = marginalDischargeCosts


class CurtailmentStrategy(ControlStrategy):
    """Control strategy that specifies a max power at which the production is curtailed"""
    maxPower = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, maxPower=None, **kwargs):

        super().__init__(**kwargs)

        if maxPower is not None:
            self.maxPower = maxPower


class PVTInstallation(Producer):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class ElectricityNetwork(EnergyNetwork):
    """Describes an complete Electricty network, without detailing the complete topology. It is a Transport capability"""
    voltage = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, voltage=None, **kwargs):

        super().__init__(**kwargs)

        if voltage is not None:
            self.voltage = voltage


class ElectricityCable(AbstractConductor):
    """Describes a representation of an electricity cable. When defining the geometry of a cable by means of a line, the first point of the line refers to the first port and the last point of the line refers to the second port."""
    length = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, length=None, **kwargs):

        super().__init__(**kwargs)

        if length is not None:
            self.length = length


class HeatNetwork(EnergyNetwork):
    """Describes an complete heat network, without detailing the complete topology. It is a Transport capability"""
    temperature = EAttribute(eType=EDouble, derived=False, changeable=True)
    temperatureMin = EAttribute(eType=EDouble, derived=False, changeable=True)
    temperatureMax = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, temperature=None, temperatureMin=None, temperatureMax=None, **kwargs):

        super().__init__(**kwargs)

        if temperature is not None:
            self.temperature = temperature

        if temperatureMin is not None:
            self.temperatureMin = temperatureMin

        if temperatureMax is not None:
            self.temperatureMax = temperatureMax


class GasNetwork(EnergyNetwork):
    """Describes an complete gas network, without detailing the complete topology. It is a Transport capability"""
    pressure = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, pressure=None, **kwargs):

        super().__init__(**kwargs)

        if pressure is not None:
            self.pressure = pressure


class Pipe(AbstractConductor):
    """Represents a pipe to transport gasses or fluids. When defining the geometry of a pipe by means of a line, the first point of the line refers to the first port and the last point of the line refers to the second port."""
    innerDiameter = EAttribute(eType=EDouble, derived=False, changeable=True, default_value=0.0)
    outerDiameter = EAttribute(eType=EDouble, derived=False, changeable=True)
    length = EAttribute(eType=EDouble, derived=False, changeable=True)
    roughness = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, innerDiameter=None, outerDiameter=None, length=None, roughness=None, **kwargs):

        super().__init__(**kwargs)

        if innerDiameter is not None:
            self.innerDiameter = innerDiameter

        if outerDiameter is not None:
            self.outerDiameter = outerDiameter

        if length is not None:
            self.length = length

        if roughness is not None:
            self.roughness = roughness


class Transformer(AbstractTransformer):
    """Electrical transformer between different voltage levels"""
    voltagePrimary = EAttribute(eType=EDouble, derived=False, changeable=True)
    voltageSecundary = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, voltagePrimary=None, voltageSecundary=None, **kwargs):

        super().__init__(**kwargs)

        if voltagePrimary is not None:
            self.voltagePrimary = voltagePrimary

        if voltageSecundary is not None:
            self.voltageSecundary = voltageSecundary


class HeatExchange(AbstractTransformer):
    """Exchange heat between two circuits"""
    LossDeltaT = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, LossDeltaT=None, **kwargs):

        super().__init__(**kwargs)

        if LossDeltaT is not None:
            self.LossDeltaT = LossDeltaT


class EConnection(AbstractConnection):
    """Electricity connection of a building. Defines the demarcation between the inhouse network and the electricity grid (location where the (smart) meter is located)"""
    EANCode = EAttribute(eType=EString, derived=False, changeable=True)

    def __init__(self, *, EANCode=None, **kwargs):

        super().__init__(**kwargs)

        if EANCode is not None:
            self.EANCode = EANCode


class HConnection(AbstractConnection):
    """Heat connection of a building. Defines the demarcation between the inhouse network and the heat grid (location where the (smart) meter is located)"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GConnection(AbstractConnection):
    """Gas connection of a building. Defines the demarcation between the inhouse network and the gas grid (location where the (smart) meter is located)"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class FuelCell(CoGeneration):
    """Defines a Fuel Cell"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class WindParc(WindTurbine):
    """Defines a wind parc of multiple turbines"""
    numberOfTurbines = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, numberOfTurbines=None, **kwargs):

        super().__init__(**kwargs)

        if numberOfTurbines is not None:
            self.numberOfTurbines = numberOfTurbines


class PVParc(PVPanel):
    """Defines a PV parc of multiple panels"""
    numberOfPanels = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, numberOfPanels=None, **kwargs):

        super().__init__(**kwargs)

        if numberOfPanels is not None:
            self.numberOfPanels = numberOfPanels


class Pump(AbstractTransformer):
    """Defines a pump, e.g. in a water or heat network"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Valve(AbstractSwitch):
    """Defines a valve, e.g. in a water, gas or heat network"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class CHP(CoGeneration):
    """Describes a Combined Heat and Power installation"""
    CHPType = EAttribute(eType=CHPTypeEnum, derived=False, changeable=True)

    def __init__(self, *, CHPType=None, **kwargs):

        super().__init__(**kwargs)

        if CHPType is not None:
            self.CHPType = CHPType


class Electrolyzer(PowerToX):
    """Defines an electrolyzer that converts electricity into hydrogen"""
    outputPressure = EAttribute(eType=EDouble, derived=False, changeable=True)
    maxLoad = EAttribute(eType=EInt, derived=False, changeable=True)
    minLoad = EAttribute(eType=EInt, derived=False, changeable=True)
    effMaxLoad = EAttribute(eType=EDouble, derived=False, changeable=True)
    effMinLoad = EAttribute(eType=EDouble, derived=False, changeable=True)

    def __init__(self, *, outputPressure=None, maxLoad=None, minLoad=None, effMaxLoad=None, effMinLoad=None, **kwargs):

        super().__init__(**kwargs)

        if outputPressure is not None:
            self.outputPressure = outputPressure

        if maxLoad is not None:
            self.maxLoad = maxLoad

        if minLoad is not None:
            self.minLoad = minLoad

        if effMaxLoad is not None:
            self.effMaxLoad = effMaxLoad

        if effMinLoad is not None:
            self.effMinLoad = effMinLoad


class PVInstallation(PVPanel):
    """Defines a Photo Voltaic Installation, e.g. roof top PV, a PV field or parc."""
    type = EAttribute(eType=PVInstallationTypeEnum, derived=False, changeable=True)
    numberOfPanels = EAttribute(eType=EInt, derived=False, changeable=True)

    def __init__(self, *, type=None, numberOfPanels=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if numberOfPanels is not None:
            self.numberOfPanels = numberOfPanels


class CircuitBraker(AbstractSwitch):
    """Defines a circuit breaker in electric transmission or distribution grids"""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class UTES(HeatStorage):

    type = EAttribute(eType=UTESTypeEnum, derived=False, changeable=True,
                      default_value=UTESTypeEnum.UNDEFINED)
    UTESPotential = EReference(ordered=True, unique=True, containment=False)

    def __init__(self, *, type=None, UTESPotential=None, **kwargs):

        super().__init__(**kwargs)

        if type is not None:
            self.type = type

        if UTESPotential is not None:
            self.UTESPotential = UTESPotential


class WaterBuffer(HeatStorage):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Joint(AbstractConductor):
    """A Joint is a means to connect AbstractConductors. This helps when these conductors have opposite Ports."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
