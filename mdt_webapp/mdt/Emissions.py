import csv, os.path, math
import numpy as np
from sklearn.neighbors import KDTree

from pollemission.copert import *

from mdt_project.settings import POL_DIR, CSV_DIR

c = Copert(POL_DIR+"input/PC_parameter.csv",
           POL_DIR+"input/LDV_parameter.csv",
           POL_DIR+"input/HDV_parameter.csv",
           POL_DIR+"input/Moto_parameter.csv")

vehicle_types = [c.vehicle_type_motorcycle,
                 c.vehicle_type_passenger_car,
                 c.vehicle_type_bus,
                 c.vehicle_type_light_commercial_vehicle,
                 c.vehicle_type_heavy_duty_vehicle]

engine_types = [c.engine_type_gasoline, c.engine_type_diesel]

copert_classes = [c.class_PRE_ECE,
                c.class_Euro_1, c.class_Euro_2, c.class_Euro_3,
                c.class_Euro_4, c.class_Euro_5, c.class_Euro_6]

engine_capacities = [c.engine_capacity_0p8_to_1p4,
                   c.engine_capacity_1p4_to_2]

# 2016 Euro class distribution (among private vehicles)according
# to "The European Emission Standards of the Car Fleet Registered
# across Scotland’s Main Cities," published in February 2017.
diesel_eu_class_distribution = [0.000/0.349,  # Pre-Euro
                                0.002/0.349,  # Euro 1
                                0.007/0.349,  # Euro 2
                                0.075/0.349,  # Euro 3
                                0.134/0.349,  # Euro 4
                                0.120/0.349,  # Euro 5
                                0.011/0.349]  # Euro 6

petrol_eu_class_distribution = [0.013/0.651,  # Pre-Euro
                                0.008/0.651,  # Euro 1
                                0.049/0.651,  # Euro 2
                                0.209/0.651,  # Euro 3
                                0.201/0.651,  # Euro 4
                                0.150/0.651,  # Euro 5
                                0.021/0.651]  # Euro 6

euro_class_distributions = [petrol_eu_class_distribution, diesel_eu_class_distribution]

def build_vehicle_kdtree(filename):
    """
    Builds a K-D tree from the UKDT count points dataset for
    finding the vehicle proportions.
    :param filename: count points file
    """
    if os.path.isfile(filename):
        coors = []
        vehicle_data = []
        with open(filename) as csvfile:

            readCSV = csv.reader(csvfile, delimiter=',')
            
            has_header = csv.Sniffer().has_header(filename)
            if has_header:
                next(readCSV)
            for row in readCSV:
                coors.append([float(row[12]), float(row[13])])
                count_data = []
                for type_index in range(19, 23):
                    count_data.append(int(row[type_index])/int(row[30]))
                count_data.append(int(row[29])/int(row[30]))
                vehicle_data.append(count_data)
        
        kdt = KDTree(np.asarray(coors))

        return kdt, vehicle_data

    else:
        print("'{0}' does not exist.".format(filename))

def calculate_net_emissions(network, vehicle_types=vehicle_types, engine_petrol_prop=0.635, temperature=9.0, type_modifiers=None):
    """
    Calculates emissions for each segment on the network.
    :param network:            network object
    :param vehicle_types:      list of copert vehicle classes to use
    :param engine_petrol_prop: proportion of petrol vehicles
    :param temperature:        ambient temperature
    :param type_modifiers:     vehicle type modifiers
    """
    segments = network.get_network_segments()

    for key in segments.keys():
        segment = segments[key]
        if not network.is_closed(key):
            calculate_seg_emissions(segment, segment.get_attributes()['vehicleProps'], vehicle_types, [engine_petrol_prop, 1 - engine_petrol_prop], temperature, type_modifiers=type_modifiers)

def calculate_seg_emissions(segment, vehicle_type_prop, vehicle_types=vehicle_types, engine_type_distribution=[0.635, 0.365], temperature=9.0, engine_capacity_distribution=0.5, type_modifiers=None):
    """
    Calculates emissions for one segment, and stores hourly
    values in their attributes dictionary.
    :param vehicle_type_prop: original vehicle type proportions
    :param vehicle_types: copert vehicle classes used
    :param engine_type_distribution: array containing petrol and diesel engine distributions
    :param engine_capacity_distribution: distribution between engine types
    :param temperature: ambient temperature
    :param type_modifiers: vehicle type modifier array
    """

    # Vehicle type proportions are multiplied by the type modifiers,
    # and the new values are calculated as a percent of their total.
    hot_emissions = []
    if type_modifiers != None and len(type_modifiers) == len(vehicle_type_prop):
        vehicle_type_prop = [a*b for a,b in zip(vehicle_type_prop,type_modifiers)]
        if sum(vehicle_type_prop)/len(vehicle_type_prop) != 0:
            total = sum(vehicle_type_prop)
            new_proportions = []
            for prop in vehicle_type_prop:
                new_proportions.append(prop/total)
            vehicle_type_prop = new_proportions

            # These new values are stored in the attributes dictionary so they
            # can be displayed in the inspector panel.
            segment.set_attribute('vehicleProps', vehicle_type_prop)

    for time_slot in segment.get_attributes()['flowData']:
        time_slot_emissions = 0
        if time_slot[3] > 0:

            # ~ Two wheeled vehicles ~ #
            if vehicle_type_prop[0] != 0:

                # Emissions for mopeds.
                two_wheeled_vehicle_emissions = c.EFMoped(c.pollutant_CO,
                                                        time_slot[1],
                                                        c.engine_type_moped_two_stroke_less_50,
                                                        c.class_Euro_3)

                # Emissions for motorcycles.
                two_wheeled_vehicle_emissions += c.EFMotorcycle(c.pollutant_CO,
                                                                time_slot[1],
                                                                c.engine_type_moto_four_stroke_more_750,
                                                                c.class_Euro_3)
                
                time_slot_emissions += (two_wheeled_vehicle_emissions * time_slot[3]) * vehicle_type_prop[0]
            
            # ~ Passenger vehicles & taxis ~ #
            for engine_type in range(2): # For both petrol and diesel
                for copert_class in range(len(copert_classes)): # For all European emissions classes
                    for engine_capacity in engine_capacities: # Engine capacity is either 0.8-1.4l or 1.4-2l
                        if (copert_classes[copert_class] != c.class_Improved_Conventional and copert_classes[copert_class] != c.class_Open_loop) or engine_capacity <= 2.0:
                            
                            # No formula available for diesel passenger cars whose
                            # engine capacity is less than 1.4 l and the copert class
                            # is Euro 1, Euro 2 or Euro 3.
                            if engine_types[engine_type] != c.engine_type_diesel and engine_capacity != c.engine_capacity_0p8_to_1p4:
                                if copert_classes[copert_class] not in [c.class_Euro_1, c.class_Euro_2, c.class_Euro_3]:
                                    
                                    # No formula for vehicles below 10kph (6.2mph) or above 130kph (80.8mph)
                                    if time_slot[1] > 10 and time_slot[1] < 130:
                                        
                                        passenger_car_emissions = c.Emission(c.pollutant_CO,
                                                                  time_slot[1],
                                                                  segment.get_attributes()['length'],
                                                                  c.vehicle_type_passenger_car,
                                                                  engine_types[engine_type],
                                                                  copert_classes[copert_class],
                                                                  engine_capacity,
                                                                  temperature)

                                        if time_slot[1] > 5 and time_slot[1] < 45 and temperature > -20:
                                            passenger_car_emissions += c.ColdStartEmissionQuotient(c.vehicle_type_passenger_car,
                                                                                                   engine_types[engine_type],
                                                                                                   c.pollutant_CO,
                                                                                                   time_slot[1],
                                                                                                   copert_classes[copert_class],
                                                                                                   engine_capacity, temperature) * passenger_car_emissions
                                        
                                        # Multiply emissions by sample size (total number of cars)
                                        passenger_car_emissions *= time_slot[3]
                                        
                                        # Multiply by proportion of engine type (petrol/diesel) & capacity (0.8-1.4l/1.4l-2)
                                        # & proportion of european emissions standards class
                                        passenger_car_emissions *= (engine_type_distribution[engine_types[engine_type]]
                                                                    * engine_capacity_distribution
                                                                    * euro_class_distributions[engine_type][copert_class])

                                        # Multiply by proportion of passenger cars
                                        time_slot_emissions += passenger_car_emissions * vehicle_type_prop[1]
            
            # ~ Buses and coaches ~ #
            if vehicle_type_prop[2] != 0:
                # The input speed must be in the range of [11.0, 86.0] <- 6.8-53.4mph
                # when calculating hot emission factors for heavy duty 
                # vehicles of type 'Urban Buses Standard 15 - 18 t' when 
                # the charge is 50% and the slope is 0%.
                if time_slot[1] > 11 and time_slot[1] < 86:
                    bus_coach_emissions = 0
                    bus_type_distribution = [448/791, 138/791, 173/791]
                    bus_classes = [c.class_hdv_Euro_III, c.class_hdv_Euro_IV, c.class_hdv_Euro_VI]
                    for bus_class in range(len(bus_classes)):
                        bus_class_emissions = c.HEFHeavyDutyVehicle(speed = time_slot[1],
                                                                    vehicle_category = c.vehicle_type_bus,
                                                                    hdv_type = c.bus_type_urban_more_18,
                                                                    hdv_copert_class = bus_classes[bus_class],
                                                                    pollutant = c.pollutant_CO,
                                                                    load = c.hdv_load_50,
                                                                    slope = 0)
                        
                        bus_coach_emissions += (bus_class_emissions * bus_type_distribution[bus_class])
                    
                    time_slot_emissions += (bus_coach_emissions * time_slot[3]) * vehicle_type_prop[2]

            # ~ Light commercial vehicles ~ #
            if vehicle_type_prop[3] != 0:
                # According to the Updated Vehicle Emission Curves Use
                # in the National Transport Model (2009), the proportion
                # of Euro classes for LGVs is:
                lgv_class_distribution = [0.002, 0.019, 0.150, 0.313, 0.516]
                # Class distribution is the same for diesel and petrol LGVs for Euro classes 2-6.
                lgv_classes = copert_classes[2:]

                lgv_emissions = 0
                for copert_class in range(len(lgv_classes)):
                    for engine_type in engine_types:
                        if copert_class != c.class_Euro_1 and time_slot[1] > 10 and time_slot[1] < 120:
                            # Cold and hot emissions are calculated seprately for LGVs.
                            lgv_class_emissions = c.HEFLightCommercialVehicle(pollutant = c.pollutant_CO,
                                                                              speed = time_slot[1],
                                                                              engine_type = engine_type,
                                                                              copert_class = lgv_classes[copert_class])
                            if time_slot[1] > 5 and time_slot[1] < 45 and temperature > -20:
                                            lgv_class_emissions += c.ColdStartEmissionQuotient(c.vehicle_type_light_commercial_vehicle,
                                                                                                   engine_types[engine_type],
                                                                                                   c.pollutant_CO,
                                                                                                   time_slot[1],
                                                                                                   lgv_classes[copert_class],
                                                                                                   engine_capacity, temperature) * lgv_class_emissions
                            lgv_emissions += (lgv_class_emissions
                                              * engine_type_distribution[engine_types[engine_type]]
                                              * lgv_class_distribution[copert_class])
                
                time_slot_emissions += (lgv_emissions * time_slot[3]) * vehicle_type_prop[3]
                                                                      
                    
            # ~ Heavy commercial vehicles ~ #
            if vehicle_type_prop[4] != 0:
                # Class distribution comes from the same report as for
                # LGVs, the Updated Vehicle Emission Curves Use
                # in the National Transport Model (2009).
                hgv_class_distribution = [0.008, 0.027, 0.203, 0.761]
                hgv_classes = [c.class_hdv_Euro_III,
                               c.class_hdv_Euro_IV,
                               c.class_hdv_Euro_V_EGR,
                               c.class_hdv_Euro_VI]

                hgv_emissions = 0

                for copert_class in range(len(hgv_classes)):
                    if time_slot[1] > 12 and time_slot[1] < 86:
                        hgv_class_emissions = c.HEFHeavyDutyVehicle(speed = time_slot[1],
                                                                    vehicle_category = c.vehicle_type_heavy_duty_vehicle,
                                                                    hdv_type = c.hdv_type_rigid_14_20,
                                                                    hdv_copert_class = hgv_classes[copert_class],
                                                                    pollutant = c.pollutant_CO,
                                                                    load = c.hdv_load_50,
                                                                    slope = c.slope_0)
                        
                        hgv_emissions += (hgv_class_emissions * hgv_class_distribution[copert_class])
                
                time_slot_emissions += (hgv_emissions * time_slot[3]) * vehicle_type_prop[4]

        hot_emissions.append(time_slot_emissions)
    
    segment.set_attribute('emissions', hot_emissions)
