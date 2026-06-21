## JIRA LINK 
>
> <https://jira.phison.com:8443/browse/XXXXX>
>
## Summary
>
>(Summarize the bug encountered concisely)
>
## Reviewer
>
> ex. Bill/Thomas
>

## Code Review
- [ ] 確認code_review.py的報告無Error
1. 確認沒有magic number 
1. 確認格式是test_case_example.py檔案 
1. 確認Pattern中沒有專案判斷式, 沒有is_support() 
1. 確認有透過Logger印訊息(warn, error, info, flow, error_lb, error_fp) 
1. 確認在library的function有標註型別 (i.e. def greeting(name: str) -> str: ) 
1. 確認新寫的lib function name，沒有和既有的衝突 
1. 確認Pattern判fail使用REPORT_FAILED(), 禁止sys.exit() 
1. 確認Feature共同function，獨立拉出一個py檔來放mutual function 
1. 確認對應功能有使用CommonPath/config_descriptor/get_smartinfo/get_flash_setting