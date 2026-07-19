"""Idempotently add 300 catalogue products using the bundled product images."""
import os
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_system.settings')
django.setup()

from products.models import Category, Product


CATALOGUE = {
    'Camera Gear': ('Sony', 'Camera and video equipment maintained and ready for rental.', 55, 180),
    'Power Tools': ('Bosch', 'Professional-grade tool kit for home and commercial projects.', 30, 120),
    'Outdoor Equipment': ('Coleman', 'Reliable outdoor equipment for trips, events, and adventures.', 22, 90),
    'Party Supplies': ('JBL', 'Event-ready party and entertainment equipment.', 40, 140),
    'Event Furniture': ('IKEA', 'Clean, durable furniture for meetings and celebrations.', 18, 70),
    'Home Appliances': ('Philips', 'Convenient appliances for short-term household needs.', 25, 100),
}

PRODUCT_TYPES = {
    'Camera Gear': ['Mirrorless Camera', 'DSLR Camera', 'Prime Lens', 'Zoom Lens', 'Tripod', 'LED Light Kit', 'Wireless Microphone', 'Camera Gimbal', 'Action Camera', 'Drone Kit'],
    'Power Tools': ['Cordless Drill', 'Circular Saw', 'Angle Grinder', 'Rotary Hammer', 'Pressure Washer', 'Tile Cutter', 'Electric Sander', 'Welding Machine', 'Ladder', 'Generator'],
    'Outdoor Equipment': ['Camping Tent', 'Sleeping Bag', 'Mountain Bicycle', 'Kayak', 'Portable Grill', 'Hiking Backpack', 'Cooler Box', 'Camping Table', 'Inflatable Boat', 'Trekking Pole Set'],
    'Party Supplies': ['Party Speaker', 'Karaoke System', 'Projector', 'Dance Floor Light', 'Smoke Machine', 'Photo Booth', 'Popcorn Machine', 'Cotton Candy Machine', 'DJ Controller', 'PA System'],
    'Event Furniture': ['Banquet Chair', 'Round Table', 'Cocktail Table', 'Sofa Set', 'Display Stand', 'Canopy Tent', 'Bar Counter', 'Red Carpet', 'Stage Platform', 'Podium'],
    'Home Appliances': ['Air Conditioner', 'Refrigerator', 'Microwave Oven', 'Washing Machine', 'Vacuum Cleaner', 'Air Purifier', 'Water Dispenser', 'Induction Cooktop', 'Room Heater', 'Stand Fan'],
}

IMAGES = ['product_images/images_3.jpg', 'product_images/images_4.jpg', 'product_images/images_5.jpg', 'product_images/images_6.jpg']


def main():
    categories = {
        name: Category.objects.get_or_create(name=name, defaults={'description': f'Rental category: {name}.'})[0]
        for name in CATALOGUE
    }
    products = []
    for number in range(1, 301):
        category_name = list(CATALOGUE)[(number - 1) % len(CATALOGUE)]
        brand, description, base_rate, base_deposit = CATALOGUE[category_name]
        item_type = PRODUCT_TYPES[category_name][((number - 1) // len(CATALOGUE)) % len(PRODUCT_TYPES[category_name])]
        name = f'{brand} {item_type} Rental #{number:03d}'
        if Product.objects.filter(name=name).exists():
            continue
        rate = Decimal(base_rate + (number % 7) * 5)
        products.append(Product(
            name=name, category=categories[category_name], brand=brand,
            manufacturer=brand, color=['Black', 'Blue', 'Silver', 'Red'][number % 4],
            size=['Compact', 'Standard', 'Professional'][number % 3],
            description=f'{description} Catalogue item {number:03d}.',
            rental_price=rate, security_deposit=Decimal(base_deposit + (number % 5) * 20),
            late_fee_rate=Decimal('5.00') + Decimal(number % 4) * Decimal('2.50'),
            image=IMAGES[(number - 1) % len(IMAGES)], is_available=True,
        ))
    Product.objects.bulk_create(products, batch_size=100)
    print(f'Added {len(products)} products. Total products: {Product.objects.count()}')


if __name__ == '__main__':
    main()
