.PHONY: get-list install run-page

get-list:
	uv run yt-transcript --input-list urls.txt --no-verify-ssl

install:
	uv pip install flask flask-cors youtube-transcript-api

run-page:
	uv run python mobile_server.py
