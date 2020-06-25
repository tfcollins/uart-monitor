import glob


uarts = glob.glob("/dev/serial/by-id/*")

with open("config.yaml", 'w') as f:
    f.write("uarts:\n")

    for uart in uarts:
        f.write('- "{}"\n'.format(uart))
