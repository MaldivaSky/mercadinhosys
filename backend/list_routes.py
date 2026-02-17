from app import create_app

app = create_app()

with open("routes.log", "w") as f:
    for rule in app.url_map.iter_rules():
        if "search" in str(rule) or "produtos" in str(rule):
            f.write(f"{rule} -> {rule.endpoint}\n")
    print("Done writing to routes.log")
