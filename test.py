
from generate_from_mongo import generate_barcode


def main():
	# Contoh singkat: buat barcode untuk ID 899721989516
	path = generate_barcode(8997219895164)
	print('Generated barcode at:', path)


if __name__ == '__main__':
	main()

