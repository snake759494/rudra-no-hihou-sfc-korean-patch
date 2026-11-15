# 빌드

Windows, Python 3.10 이상에서 확인했습니다.

```powershell
pip install -r requirements.txt
copy '원본 경로\Rudra no Hihou (Japan).sfc' .   # 저장소 루트에 원본 ROM을 둡니다
python tools/fetch_tools.py                       # 갈무리 v2.40.3을 work/fonts/에 받고 해시 대조
python tools/build.py 'Rudra no Hihou (Japan).sfc' 'work/Rudra no Hihou (Korean).sfc'
xdelta3 -e -0 -f -s 'Rudra no Hihou (Japan).sfc' 'work/Rudra no Hihou (Korean).sfc' Rudra_no_Hihou_SFC_KR.xdelta
```

- `build.py`는 원본 ROM(4,194,304바이트, 헤더 없음)의 SHA-256을 먼저 검사합니다. 글꼴 판이 다르면 결과 ROM도 달라집니다.
- 출력의 `SHA-256` 줄이 README의 `output`과 같으면 릴리즈와 동일한 ROM입니다.

## 번역 파일 형식

- `translation/d00_ko.txt`~`d12_ko.txt`(대사), `sys_ko.txt`(시스템 문장): `원본주소(16진)<TAB>한국어`. `¶` 줄바꿈, `{06}` 키 대기, `{05}` 새 창, `{0c}` 숫자, `{0d}` 아이템 이름, `<P0>`~`<P3>` 주인공 이름, `<W번호>` 플레이어가 등록한 언령 단어, 그 밖의 `{XX}`·`{XX:YY}`는 원본 제어 바이트입니다. 대사 창은 한 줄 24칸입니다.
- `names_t2.txt`(아이템·장비), `names_t8.txt`(몬스터): `번호<TAB>이름`. `names_misc.txt`·`names_big.txt`: `표:번호<TAB>이름`. 메뉴에 나오는 표는 1바이트 글자만 쓸 수 있습니다.
- `labels_ko.txt`: 메뉴 그림 글자 `타일맵주소<TAB>라벨`.
- `prologue_ko.txt`: 오프닝 프롤로그 21줄.
- `menu_base.txt`·`menu_extra.txt`·`pool_punct.txt`: 1바이트 코드에 배정할 음절·기호 목록.

## 검증 도구

`tools/emu.py`는 검증용 헤드리스 snes9x 하네스이며 `snes9x_libretro.dll`을 따로 받아 `tools/`에 두어야 합니다(저장소에 포함하지 않음). `d65.py`(역어셈블), `cpu.py`·`tr.py`(65816 추적), `a65.py`(어셈블)는 분석용입니다.
