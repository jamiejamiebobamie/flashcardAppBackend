def parse_cookies():
    cookies = {}
    with open("./src/quizletCookies.md", "r") as f:
        lines = f.read().split("\n")
        for line in lines:
            if len(line):
                tokens = line.split("\t")
                key = tokens[0]
                value = tokens[1]
                cookies[key] = value
    return cookies
