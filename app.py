from flask import Flask, request, render_template_string, redirect
import logging
import requests
import os
from datetime import datetime

# Firebase Admin SDK import'ları
import firebase_admin
from firebase_admin import credentials, db
import json

# HTML string'leri EN ÜSTE koy (önce tanımlansınlar)
HOME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NGL - Anonim Mesaj</title>
    <style>
        body {
            background: linear-gradient(135deg, #000000, #1a0033);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        h1 {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        input[type="text"] {
            width: 80%;
            max-width: 400px;
            padding: 15px;
            font-size: 1.2rem;
            border: none;
            border-radius: 50px;
            background: rgba(255,255,255,0.1);
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        input[type="text"]::placeholder { color: rgba(255,255,255,0.6); }
        button {
            padding: 16px 50px;
            background: linear-gradient(90deg, #ff00cc, #3333ff);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.3rem;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { transform: scale(1.05); }
        .info {
            margin-top: 30px;
            font-size: 0.9rem;
            opacity: 0.7;
            color: #ccc;
        }
    </style>
</head>
<body>
    <h1>NGL Anonim</h1>
    <p>Kullanıcı adını gir (isteğe bağlı)</p>
    <form method="GET" action="/">
        <input type="text" name="username" placeholder="Kullanıcı adı gir (örn: muhammedemin)" autocomplete="off">
        <button type="submit">Devam Et</button>
    </form>
    <div class="info">Boş bırakırsan rastgele bir isim kullanılır</div>
</body>
</html>
"""

NGL_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NGL</title>
    <style>
        body {
            background: linear-gradient(135deg, #000000, #1a0033);
            color: white;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center
