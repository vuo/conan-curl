#include <stdio.h>
#include <curl/curl.h>

int main()
{
	CURLcode ret = curl_global_init(CURL_GLOBAL_DEFAULT);
	if (ret != CURLE_OK)
	{
		fprintf(stderr, "Error initializing cURL: %s\n", curl_easy_strerror(ret));
		return -1;
	}

	printf("Successfully initialized cURL %s\n", curl_version());

	curl_global_cleanup();
	return 0;
}
