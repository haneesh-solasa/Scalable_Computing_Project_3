import pandas as pd
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str)
    args=parser.parse_args()
    name = args.name
    weather = pd.read_csv('2022_2.csv')
    filtered_weather = weather[weather['ID'] == name]
    filtered_weather = filtered_weather[filtered_weather['D'] >= 48]
    filtered_weather.to_csv(f'{name}.csv', index=False)

if __name__ == '__main__':
    main()
