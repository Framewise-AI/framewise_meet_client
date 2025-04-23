import sys

def main():
    if len(sys.argv) > 1:
        print(sys.argv[1])
    else:
        print("No argument provided. Usage: python kk.py <argument>")

if __name__ == "__main__":
    main()