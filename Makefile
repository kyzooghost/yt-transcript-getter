.PHONY: get-list

get-list:
	uv run yt-transcript --input-list urls.txt --no-verify-ssl
