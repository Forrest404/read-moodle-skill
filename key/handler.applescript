on open location theURL
	set scriptPath to POSIX path of (path to resource "store_token.sh")
	do shell script "/bin/zsh " & quoted form of scriptPath & " " & quoted form of theURL
end open location
