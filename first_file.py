from flask import Flask, request, render_template_string

app = Flask(__name__)

# Page HTML avec un formulaire
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Serveur Web</title>
</head>
<body>
    <h1>Entrez une valeur</h1>
    <form method="POST">
        <input type="text" name="value" placeholder="Entrez une valeur" required>
        <button type="submit">Envoyer</button>
    </form>
    {% if value %}
    <h2>Valeur reçue : {{ value }}</h2>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    value = None
    if request.method == "POST":
        value = request.form.get("value")
    return render_template_string(html_template, value=value)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)