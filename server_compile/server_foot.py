if __name__ == '__main__':
    with open(CONFIG_PATH,'r') as config:
        port = yaml.safe_load(config)['server_port']
    app.run(host='0.0.0.0', port=port)
