# ゴミ箱に移動するための関数
function Move-ToRecycleBin {
    param (
        [string]$FilePath
    )
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.Namespace(10)  # 10はゴミ箱フォルダ
    $item = $shell.NameSpace((Get-Item $FilePath).DirectoryName).ParseName((Get-Item $FilePath).Name)
    $item.InvokeVerb("delete")  # ゴミ箱に移動する
}

# カレントディレクトリ以下の .blend1, .blend2, .blend3... ファイルを再帰的に検索
$files = Get-ChildItem -Recurse -Filter "*.blend*" | Where-Object { $_.Name -match "\.blend[1-9][0-9]?$" -and $_.Name -notmatch "\.blend$" }

if ($files) {
    Write-Host "The following .blend1, .blend2, .blend3... files will be moved to the Recycle Bin:" -ForegroundColor Yellow
    $files | ForEach-Object {
        Write-Host $_.FullName
    }

    # ユーザーに確認
    $confirm = Read-Host "Do you want to move these files to the Recycle Bin? (yes/no)"
    if ($confirm -eq "yes") {
        $files | ForEach-Object {
            Move-ToRecycleBin -FilePath $_.FullName
            Write-Host "Moved to Recycle Bin: $($_.FullName)"
        }
        Write-Host "All .blend1, .blend2, .blend3... files have been moved to the Recycle Bin."
    } else {
        Write-Host "No files were moved." -ForegroundColor Green
    }
} else {
    Write-Host "No .blend1, .blend2, .blend3... files found." -ForegroundColor Green
}

# 最後のメッセージ後に停止
Write-Host "Process complete. Press any key to exit." -ForegroundColor Cyan
[System.Console]::ReadKey() | Out-Null
