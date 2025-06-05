if exist "%USERPROFILE%\ZAP\.ZAP_JVM.properties" (
	set /p jvmopts=< "%USERPROFILE%\ZAP\.ZAP_JVM.properties"
) else (
	set jvmopts=-Xmx512m
)

java %jvmopts% -jar zap-2.16.1.jar %*
