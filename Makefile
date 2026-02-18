.PHONY: get-list install run-page phone-page clean empty

get-list:
	UV_INSECURE_HOST="pypi.org files.pythonhosted.org" uv run yt-transcript --input-list urls.txt --no-verify-ssl

install:
	uv pip install flask flask-cors youtube-transcript-api

run-page:
	uv run python mobile_server.py

phone-page:
	python mobile_server.py

clean:
	rm -rf output/*

empty:
	mkdir -p output
	touch output/transcript-1.md
