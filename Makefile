.PHONY: get-list install run-page clean

get-list:
	uv run yt-transcript --input-list urls.txt --no-verify-ssl

install:
	uv pip install flask flask-cors youtube-transcript-api

run-page:
	uv run python mobile_server.py

clean:
	rm -rf output/
