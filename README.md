# NOVA v1.1

Windows용 모의 자동매매/주식 분석 데스크톱 앱입니다. 실제 증권사 주문 기능은 포함하지 않습니다.

## v1.1

- Stock-specific ML + Global Model ensemble
- Data Guard: 결측/중복/OHLC 오류/극단 변동/데이터 부족 검사
- Confidence Engine: 데이터 품질 + 검증 성능 + 모델 일치도
- 250거래일 미만이면 Stock Model을 끄고 Global Model 중심으로 자동 후퇴
- 모의계좌/규칙 DB는 `%LOCALAPPDATA%\NOVA\nova.db`에 저장
- GitHub Release 기반 자동 업데이트 + SHA-256 검증
- AI Advisor는 권고만 하며 직접 주문/규칙 수정 권한이 없음

## 실행

Python 3.11+에서 `install_and_run.bat`을 실행합니다. 이후에는 `run.bat`으로 실행할 수 있습니다.

## 자동 업데이트

NOVA는 `kimyejun978-tech/NOVA`의 최신 GitHub Release를 확인합니다.

이 저장소의 `.github/workflows/release.yml`은 `VERSION`과 `release/NOVA-Source.zip`이 갱신되면 해당 버전의 Release를 자동 생성/갱신하도록 구성합니다. `NOVA-Windows.zip`을 추가하면 EXE 배포 자산도 같은 Release에 포함할 수 있습니다.

모의계좌 데이터는 프로그램 폴더와 분리되어 있어 업데이트 시 유지됩니다.

## Safety

- 모의 주문 전용
- Kill Switch
- 1회 최대 주문금액
- 종목 최대 비중
- 동일 종목 주문 cooldown
- 자동 가격 규칙은 성공 체결 후 기본적으로 one-shot OFF
- Advisor는 Broker/Rule Engine 객체를 직접 참조하지 않음

## 주의

시장 데이터는 지연/누락될 수 있으며 NOVA의 ML 출력은 과거 데이터 기반 모의분석입니다. 미래 가격이나 수익을 보장하지 않습니다.
