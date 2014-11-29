
@rem Copyright (c) 2011-2014 the developers of Aqualid project
@echo off

IF [%AQL_RUN_SCRIPT%] == [YES] (
  SET AQL_RUN_SCRIPT=
  python -c "import aql; aql.main()" %*

) ELSE (
  REM Workaround for an interactive prompt "Terminate batch script? (Y/N)" when CTRL+C is pressed
  SET AQL_RUN_SCRIPT=YES
  CALL %0 %* <NUL
)
