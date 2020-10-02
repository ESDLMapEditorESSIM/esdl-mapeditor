from src.process_es_area_bld import calc_possible_locations_in_area
from src.shape import Shape

if __name__ == '__main__':
    polygon = Shape.create([[{'lat': 53.24903770374274, 'lng': 6.07997256161518},
                             {'lat': 53.00200032254604, 'lng': 6.036034118922504},
                             {'lat': 52.98548065305836, 'lng': 6.431480103156676},
                             {'lat': 53.216181402122956, 'lng': 6.404018576473748}]])

    loc_list = calc_possible_locations_in_area(polygon, 10)
    for loc in loc_list:
        print(list(loc.coords))