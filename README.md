# vodafoneMobileApi

I encountered a challenge while trying to track my mobile data usage: the carrier's mobile app implemented root-checking. However, I found a workaround by modifying the APK file to bypass this restriction, allowing me to use the app for a few weeks.

Unfortunately, I hit another roadblock when the app required the latest update for access. To tackle this issue, I turned my attention towards extracting data from the web API. This proved difficult due to Google Captcha protection.

I then discovered that the mobile API didn't have Captcha protection, and even though the app implemented SSL pinning, I managed to work around it by patching and intercepting the traffic.

However, my progress was halted when the app started crashing after retrieving the token. I considered decompiling the Java code to interact with the API but couldn't due to time constraints.

Nonetheless, this project was quite an interesting challenge. Perhaps in the future, either I or someone else will pick it up again and continue exploring the possibilities.

![image](https://github.com/palmarci/vodafoneMobileApi/assets/20556689/b7846391-2470-4fa1-b335-ba8ad9116b62)
