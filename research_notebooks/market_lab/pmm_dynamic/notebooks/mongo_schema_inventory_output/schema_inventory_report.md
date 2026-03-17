# MongoDB Estate Schema Inventory Report

Generated UTC: 2026-03-17T21:49:36.019134+00:00

## Summary

- **databases_visible**: 4
- **collections_and_views**: 8
- **indexes**: 20
- **observed_field_paths**: 186
- **generated_utc**: 2026-03-17T21:49:36.019134+00:00

## Notes

- MongoDB is schemaless by default; field-path results are **observed**, not guaranteed unless validators are enforced.
- `schema_is_exhaustive_for_collection = True` only indicates the collection was fully scanned under the current settings.
- When a collection is sampled, the schema report may omit rare fields.

## Databases

| database | sizeOnDisk | empty | db_collections | db_views | db_objects | db_dataSize | db_storageSize | db_indexes | db_indexSize | dbStats_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admin | 102400 | False | 2 | 0 | 3 | 628.0 | 40960.0 | 3 | 61440.0 |  |
| config | 110592 | False | 1 | 0 | 6 | 792.0 | 36864.0 | 2 | 73728.0 |  |
| local | 73728 | False | 1 | 0 | 4 | 9497.0 | 36864.0 | 1 | 36864.0 |  |
| quants_lab | 1133674496 | False | 4 | 0 | 5704656 | 2255310295.0 | 750882816.0 | 14 | 382791680.0 |  |

## Collections / Views

| database | collection | collection_type | estimated_document_count | scan_mode | documents_scanned_for_schema | schema_is_exhaustive_for_collection | observed_field_paths | coll_nindexes | coll_storageSize | validator_json | timeseries_json | view_on | sample_file | schema_file | scan_error | catalog_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admin | system.users | collection | 1 | full | 1 | True | 19.0 | 2 | 20480 | null | null |  | mongo_schema_inventory_output/samples/admin/system.users.json | mongo_schema_inventory_output/schemas/admin/system.users.json |  |  |
| admin | system.version | collection | 2 | full | 2 | True | 3.0 | 1 | 20480 | null | null |  | mongo_schema_inventory_output/samples/admin/system.version.json | mongo_schema_inventory_output/schemas/admin/system.version.json |  |  |
| config | system.sessions | collection | 6 | full | 0 | False |  | 2 | 36864 | null | null |  |  | mongo_schema_inventory_output/schemas/config/system.sessions.json | OperationFailure: not authorized on config to execute command { find: "system.sessions", filter: {}, lsid: { id: UUID("bf7818fd-a205-41a1-b521-153a72212700") }, $db: "config" }, full error: {'ok': 0.0, 'errmsg': 'not authorized on config to execute command { find: "system.sessions", filter: {}, lsid: { id: UUID("bf7818fd-a205-41a1-b521-153a72212700") }, $db: "config" }', 'code': 13, 'codeName': 'Unauthorized'} |  |
| local | startup_log | collection | 4 | full | 4 | True | 52.0 | 1 | 36864 | null | null |  | mongo_schema_inventory_output/samples/local/startup_log.json | mongo_schema_inventory_output/schemas/local/startup_log.json |  |  |
| quants_lab | candle_features | collection | 32237 | sample | 5000 | False | 47.0 | 3 | 7954432 | null | null |  | mongo_schema_inventory_output/samples/quants_lab/candle_features.json | mongo_schema_inventory_output/schemas/quants_lab/candle_features.json |  |  |
| quants_lab | candles | collection | 4841278 | sample | 5000 | False | 23.0 | 5 | 683122688 | null | null |  | mongo_schema_inventory_output/samples/quants_lab/candles.json | mongo_schema_inventory_output/schemas/quants_lab/candles.json |  |  |
| quants_lab | market_trades | collection | 831132 | sample | 5000 | False | 23.0 | 4 | 59768832 | null | null |  | mongo_schema_inventory_output/samples/quants_lab/market_trades.json | mongo_schema_inventory_output/schemas/quants_lab/market_trades.json |  |  |
| quants_lab | symbol_metadata | collection | 33 | full | 33 | True | 19.0 | 2 | 36864 | null | null |  | mongo_schema_inventory_output/samples/quants_lab/symbol_metadata.json | mongo_schema_inventory_output/schemas/quants_lab/symbol_metadata.json |  |  |

## Indexes

| database | collection | index_name | index_keys | unique | sparse | hidden | expireAfterSeconds | partialFilterExpression_json |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admin | system.users | _id_ | _id:1 | False | False | False |  | null |
| admin | system.users | user_1_db_1 | user:1, db:1 | True | False | False |  | null |
| admin | system.version | _id_ | _id:1 | False | False | False |  | null |
| config | system.sessions | _id_ | _id:1 | False | False | False |  | null |
| config | system.sessions | lsidTTLIndex | lastUse:1 | False | False | False | 1800.0 | null |
| local | startup_log | _id_ | _id:1 | False | False | False |  | null |
| quants_lab | candle_features | _id_ | _id:1 | False | False | False |  | null |
| quants_lab | candle_features | idx_connector_pair_interval_ts | connector:1, trading_pair:1, interval:1, timestamp:1 | True | False | False |  | null |
| quants_lab | candle_features | idx_latest_ts | connector:1, trading_pair:1, interval:1, timestamp:-1 | False | False | False |  | null |
| quants_lab | candles | _id_ | _id:1 | False | False | False |  | null |
| quants_lab | candles | idx_base_quote_interval_ts | base_asset:1, quote_asset:1, interval:1, timestamp:1 | False | False | False |  | null |
| quants_lab | candles | idx_connector_pair_interval_ts | connector:1, trading_pair:1, interval:1, timestamp:1 | True | False | False |  | null |
| quants_lab | candles | idx_latest_ts | connector:1, trading_pair:1, interval:1, timestamp:-1 | False | False | False |  | null |
| quants_lab | candles | idx_pair_interval_ts | trading_pair:1, interval:1, timestamp:1 | False | False | False |  | null |
| quants_lab | market_trades | _id_ | _id:1 | False | False | False |  | null |
| quants_lab | market_trades | idx_connector_pair_tradeid | connector:1, trading_pair:1, trade_id:1 | True | False | False |  | null |
| quants_lab | market_trades | idx_pair_timestamp_asc | connector:1, trading_pair:1, timestamp:1 | False | False | False |  | null |
| quants_lab | market_trades | idx_pair_timestampms_desc | connector:1, trading_pair:1, timestampms:-1 | False | False | False |  | null |
| quants_lab | symbol_metadata | _id_ | _id:1 | False | False | False |  | null |
| quants_lab | symbol_metadata | idx_connector_pair | connector:1, trading_pair:1 | True | False | False |  | null |

## Observed Field Paths

| database | collection | path | parent_path | depth | documents_scanned_for_schema | documents_with_field | presence_ratio_in_scan | observed_required_in_scan | types | examples | scan_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admin | system.users | _id |  | 0 | 1 | 1 | 1.0 | True | string | "admin.admin" | full |
| admin | system.users | credentials |  | 0 | 1 | 1 | 1.0 | True | object | {"SCRAM-SHA-1": {"iterationCount": 10000, "salt": "7NaliXi2Wn5Ivkgb/1XS5Q==", "storedKey": "s77puzNwvzhD8Zv2MM3JB93EVBI=", "serverKey": "Gmh0J2vEpWpXxrjq9X55IPxtJGs="}, "SCRAM-SHA-256": {"iterationCount": 15000, "salt": "WmYSY1lZx+NZC0iw... | full |
| admin | system.users | credentials.SCRAM-SHA-1 | credentials | 1 | 1 | 1 | 1.0 | True | object | {"iterationCount": 10000, "salt": "7NaliXi2Wn5Ivkgb/1XS5Q==", "storedKey": "s77puzNwvzhD8Zv2MM3JB93EVBI=", "serverKey": "Gmh0J2vEpWpXxrjq9X55IPxtJGs="} | full |
| admin | system.users | credentials.SCRAM-SHA-1.iterationCount | credentials.SCRAM-SHA-1 | 2 | 1 | 1 | 1.0 | True | int | 10000 | full |
| admin | system.users | credentials.SCRAM-SHA-1.salt | credentials.SCRAM-SHA-1 | 2 | 1 | 1 | 1.0 | True | string | "7NaliXi2Wn5Ivkgb/1XS5Q==" | full |
| admin | system.users | credentials.SCRAM-SHA-1.serverKey | credentials.SCRAM-SHA-1 | 2 | 1 | 1 | 1.0 | True | string | "Gmh0J2vEpWpXxrjq9X55IPxtJGs=" | full |
| admin | system.users | credentials.SCRAM-SHA-1.storedKey | credentials.SCRAM-SHA-1 | 2 | 1 | 1 | 1.0 | True | string | "s77puzNwvzhD8Zv2MM3JB93EVBI=" | full |
| admin | system.users | credentials.SCRAM-SHA-256 | credentials | 1 | 1 | 1 | 1.0 | True | object | {"iterationCount": 15000, "salt": "WmYSY1lZx+NZC0iwUKr+bGbEAKcx4bzLVtT1cQ==", "storedKey": "6z8tfXt/PBHz30PXC3a4hgVzeU2HYILlxM/llhF0JwI=", "serverKey": "BFoRy94qcT5CYFdrIEsAi2TCPPUmhKj9RA37sLjLh9U="} | full |
| admin | system.users | credentials.SCRAM-SHA-256.iterationCount | credentials.SCRAM-SHA-256 | 2 | 1 | 1 | 1.0 | True | int | 15000 | full |
| admin | system.users | credentials.SCRAM-SHA-256.salt | credentials.SCRAM-SHA-256 | 2 | 1 | 1 | 1.0 | True | string | "WmYSY1lZx+NZC0iwUKr+bGbEAKcx4bzLVtT1cQ==" | full |
| admin | system.users | credentials.SCRAM-SHA-256.serverKey | credentials.SCRAM-SHA-256 | 2 | 1 | 1 | 1.0 | True | string | "BFoRy94qcT5CYFdrIEsAi2TCPPUmhKj9RA37sLjLh9U=" | full |
| admin | system.users | credentials.SCRAM-SHA-256.storedKey | credentials.SCRAM-SHA-256 | 2 | 1 | 1 | 1.0 | True | string | "6z8tfXt/PBHz30PXC3a4hgVzeU2HYILlxM/llhF0JwI=" | full |
| admin | system.users | db |  | 0 | 1 | 1 | 1.0 | True | string | "admin" | full |
| admin | system.users | roles |  | 0 | 1 | 1 | 1.0 | True | array | [{"role": "root", "db": "admin"}] | full |
| admin | system.users | roles[] | roles | 1 | 1 | 1 | 1.0 | True | object | {"role": "root", "db": "admin"} | full |
| admin | system.users | roles[].db | roles[] | 2 | 1 | 1 | 1.0 | True | string | "admin" | full |
| admin | system.users | roles[].role | roles[] | 2 | 1 | 1 | 1.0 | True | string | "root" | full |
| admin | system.users | user |  | 0 | 1 | 1 | 1.0 | True | string | "admin" | full |
| admin | system.users | userId |  | 0 | 1 | 1 | 1.0 | True | bytes | {"$binary": {"base64": "4MbmB4zFSFyZQrGK6cfDaA==", "subType": "04"}} | full |
| admin | system.version | _id |  | 0 | 2 | 2 | 1.0 | True | string | "featureCompatibilityVersion" \|\| "authSchema" | full |
| admin | system.version | currentVersion |  | 0 | 2 | 1 | 0.5 | False | int | 5 | full |
| admin | system.version | version |  | 0 | 2 | 1 | 0.5 | False | string | "7.0" | full |
| local | startup_log | _id |  | 0 | 4 | 4 | 1.0 | True | string | "02f45e4d741e-1772486063935" \|\| "02f45e4d741e-1772486066930" \|\| "b12b5d1b86ac-1773113207713" | full |
| local | startup_log | buildinfo |  | 0 | 4 | 4 | 1.0 | True | object | {"version": "7.0.30", "gitVersion": "67480f41dfa5802ce14af5c95bd0e9826d3b2131", "modules": [], "allocator": "tcmalloc", "javascriptEngine": "mozjs", "sysInfo": "deprecated", "versionArray": [7, 0, 30, 0], "openssl": {"running": "OpenSSL ... | full |
| local | startup_log | buildinfo.allocator | buildinfo | 1 | 4 | 4 | 1.0 | True | string | "tcmalloc" | full |
| local | startup_log | buildinfo.bits | buildinfo | 1 | 4 | 4 | 1.0 | True | int | 64 | full |
| local | startup_log | buildinfo.buildEnvironment | buildinfo | 1 | 4 | 4 | 1.0 | True | object | {"distmod": "ubuntu2204", "distarch": "x86_64", "cc": "/opt/mongodbtoolchain/v4/bin/gcc: gcc (GCC) 11.3.0", "ccflags": "-Werror -include mongo/platform/basic.h -ffp-contract=off -fasynchronous-unwind-tables -g2 -Wall -Wsign-compare -Wno-... | full |
| local | startup_log | buildinfo.buildEnvironment.cc | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "/opt/mongodbtoolchain/v4/bin/gcc: gcc (GCC) 11.3.0" | full |
| local | startup_log | buildinfo.buildEnvironment.ccflags | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "-Werror -include mongo/platform/basic.h -ffp-contract=off -fasynchronous-unwind-tables -g2 -Wall -Wsign-compare -Wno-unknown-pragmas -Winvalid-pch -gdwarf-5 -fno-omit-frame-pointer -fno-strict-aliasing -O2 -march=sandybridge -mtune=gene... | full |
| local | startup_log | buildinfo.buildEnvironment.cppdefines | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "SAFEINT_USE_INTRINSICS 0 PCRE2_STATIC NDEBUG _XOPEN_SOURCE 700 _GNU_SOURCE _FORTIFY_SOURCE 2 ABSL_FORCE_ALIGNED_ACCESS BOOST_ENABLE_ASSERT_DEBUG_HANDLER BOOST_FILESYSTEM_NO_CXX20_ATOMIC_REF BOOST_LOG_NO_SHORTHAND_NAMES BOOST_LOG_USE_NAT... | full |
| local | startup_log | buildinfo.buildEnvironment.cxx | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "/opt/mongodbtoolchain/v4/bin/g++: g++ (GCC) 11.3.0" | full |
| local | startup_log | buildinfo.buildEnvironment.cxxflags | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "-Woverloaded-virtual -Wpessimizing-move -Wno-maybe-uninitialized -fsized-deallocation -Wno-deprecated -std=c++20" | full |
| local | startup_log | buildinfo.buildEnvironment.distarch | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "x86_64" | full |
| local | startup_log | buildinfo.buildEnvironment.distmod | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "ubuntu2204" | full |
| local | startup_log | buildinfo.buildEnvironment.linkflags | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "-Wl,--fatal-warnings -B/opt/mongodbtoolchain/v4/bin -gdwarf-5 -pthread -Wl,-z,now -fuse-ld=lld -fstack-protector-strong -gdwarf64 -Wl,--build-id -Wl,--hash-style=gnu -Wl,-z,noexecstack -Wl,--warn-execstack -Wl,-z,relro -Wl,--compress-de... | full |
| local | startup_log | buildinfo.buildEnvironment.target_arch | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "x86_64" | full |
| local | startup_log | buildinfo.buildEnvironment.target_os | buildinfo.buildEnvironment | 2 | 4 | 4 | 1.0 | True | string | "linux" | full |
| local | startup_log | buildinfo.debug | buildinfo | 1 | 4 | 4 | 1.0 | True | bool | false | full |
| local | startup_log | buildinfo.gitVersion | buildinfo | 1 | 4 | 4 | 1.0 | True | string | "67480f41dfa5802ce14af5c95bd0e9826d3b2131" | full |
| local | startup_log | buildinfo.javascriptEngine | buildinfo | 1 | 4 | 4 | 1.0 | True | string | "mozjs" | full |
| local | startup_log | buildinfo.maxBsonObjectSize | buildinfo | 1 | 4 | 4 | 1.0 | True | int | 16777216 | full |
| local | startup_log | buildinfo.modules | buildinfo | 1 | 4 | 4 | 1.0 | True | array | [] | full |
| local | startup_log | buildinfo.openssl | buildinfo | 1 | 4 | 4 | 1.0 | True | object | {"running": "OpenSSL 3.0.2 15 Mar 2022", "compiled": "OpenSSL 3.0.2 15 Mar 2022"} | full |
| local | startup_log | buildinfo.openssl.compiled | buildinfo.openssl | 2 | 4 | 4 | 1.0 | True | string | "OpenSSL 3.0.2 15 Mar 2022" | full |
| local | startup_log | buildinfo.openssl.running | buildinfo.openssl | 2 | 4 | 4 | 1.0 | True | string | "OpenSSL 3.0.2 15 Mar 2022" | full |
| local | startup_log | buildinfo.storageEngines | buildinfo | 1 | 4 | 4 | 1.0 | True | array | ["devnull", "wiredTiger"] | full |
| local | startup_log | buildinfo.storageEngines[] | buildinfo.storageEngines | 2 | 4 | 4 | 1.0 | True | string | "devnull" \|\| "wiredTiger" | full |
| local | startup_log | buildinfo.sysInfo | buildinfo | 1 | 4 | 4 | 1.0 | True | string | "deprecated" | full |
| local | startup_log | buildinfo.version | buildinfo | 1 | 4 | 4 | 1.0 | True | string | "7.0.30" | full |
| local | startup_log | buildinfo.versionArray | buildinfo | 1 | 4 | 4 | 1.0 | True | array | [7, 0, 30, 0] | full |
| local | startup_log | buildinfo.versionArray[] | buildinfo.versionArray | 2 | 4 | 4 | 1.0 | True | int | 7 \|\| 0 \|\| 30 | full |
| local | startup_log | cmdLine |  | 0 | 4 | 4 | 1.0 | True | object | {"net": {"bindIp": "127.0.0.1", "port": 27017, "tls": {"mode": "disabled"}}, "processManagement": {"fork": true, "pidFilePath": "/tmp/docker-entrypoint-temp-mongod.pid"}, "storage": {"wiredTiger": {"engineConfig": {"cacheSizeGB": 2.0}}},... \|\| {"net": {"bindIp": "*"}, "security": {"authorization": "enabled"}, "storage": {"wiredTiger": {"engineConfig": {"cacheSizeGB": 2.0}}}} | full |
| local | startup_log | cmdLine.net | cmdLine | 1 | 4 | 4 | 1.0 | True | object | {"bindIp": "127.0.0.1", "port": 27017, "tls": {"mode": "disabled"}} \|\| {"bindIp": "*"} | full |
| local | startup_log | cmdLine.net.bindIp | cmdLine.net | 2 | 4 | 4 | 1.0 | True | string | "127.0.0.1" \|\| "*" | full |
| local | startup_log | cmdLine.net.port | cmdLine.net | 2 | 4 | 1 | 0.25 | False | int | 27017 | full |
| local | startup_log | cmdLine.net.tls | cmdLine.net | 2 | 4 | 1 | 0.25 | False | object | {"mode": "disabled"} | full |
| local | startup_log | cmdLine.net.tls.mode | cmdLine.net.tls | 3 | 4 | 1 | 0.25 | False | string | "disabled" | full |
| local | startup_log | cmdLine.processManagement | cmdLine | 1 | 4 | 1 | 0.25 | False | object | {"fork": true, "pidFilePath": "/tmp/docker-entrypoint-temp-mongod.pid"} | full |
| local | startup_log | cmdLine.processManagement.fork | cmdLine.processManagement | 2 | 4 | 1 | 0.25 | False | bool | true | full |
| local | startup_log | cmdLine.processManagement.pidFilePath | cmdLine.processManagement | 2 | 4 | 1 | 0.25 | False | string | "/tmp/docker-entrypoint-temp-mongod.pid" | full |
| local | startup_log | cmdLine.security | cmdLine | 1 | 4 | 3 | 0.75 | False | object | {"authorization": "enabled"} | full |
| local | startup_log | cmdLine.security.authorization | cmdLine.security | 2 | 4 | 3 | 0.75 | False | string | "enabled" | full |
| local | startup_log | cmdLine.storage | cmdLine | 1 | 4 | 4 | 1.0 | True | object | {"wiredTiger": {"engineConfig": {"cacheSizeGB": 2.0}}} | full |
| local | startup_log | cmdLine.storage.wiredTiger | cmdLine.storage | 2 | 4 | 4 | 1.0 | True | object | {"engineConfig": {"cacheSizeGB": 2.0}} | full |
| local | startup_log | cmdLine.storage.wiredTiger.engineConfig | cmdLine.storage.wiredTiger | 3 | 4 | 4 | 1.0 | True | object | {"cacheSizeGB": 2.0} | full |
| local | startup_log | cmdLine.storage.wiredTiger.engineConfig.cacheSizeGB | cmdLine.storage.wiredTiger.engineConfig | 4 | 4 | 4 | 1.0 | True | double | 2.0 | full |
| local | startup_log | cmdLine.systemLog | cmdLine | 1 | 4 | 1 | 0.25 | False | object | {"destination": "file", "logAppend": true, "path": "/proc/1/fd/1"} | full |
| local | startup_log | cmdLine.systemLog.destination | cmdLine.systemLog | 2 | 4 | 1 | 0.25 | False | string | "file" | full |
| local | startup_log | cmdLine.systemLog.logAppend | cmdLine.systemLog | 2 | 4 | 1 | 0.25 | False | bool | true | full |
| local | startup_log | cmdLine.systemLog.path | cmdLine.systemLog | 2 | 4 | 1 | 0.25 | False | string | "/proc/1/fd/1" | full |
| local | startup_log | hostname |  | 0 | 4 | 4 | 1.0 | True | string | "02f45e4d741e" \|\| "b12b5d1b86ac" \|\| "aa8895121acf" | full |
| local | startup_log | pid |  | 0 | 4 | 4 | 1.0 | True | int | 28 \|\| 1 | full |
| local | startup_log | startTime |  | 0 | 4 | 4 | 1.0 | True | date | {"$date": "2026-03-02T21:14:23Z"} \|\| {"$date": "2026-03-02T21:14:26Z"} \|\| {"$date": "2026-03-10T03:26:47Z"} | full |
| local | startup_log | startTimeLocal |  | 0 | 4 | 4 | 1.0 | True | string | "Mon Mar 2 22:14:23.935" \|\| "Mon Mar 2 22:14:26.930" \|\| "Tue Mar 10 04:26:47.713" | full |
| quants_lab | candle_features | _id |  | 0 | 5000 | 5000 | 1.0 | True | objectId | {"$oid": "69b8c36cf7f2f0931fa02495"} \|\| {"$oid": "69b8c36cf7f2f0931fa02496"} \|\| {"$oid": "69b8c36cf7f2f0931fa02497"} | sample |
| quants_lab | candle_features | ask_top_qty |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | base_asset |  | 0 | 5000 | 5000 | 1.0 | True | string | "ETH" \|\| "XNV" \|\| "GHOST" | sample |
| quants_lab | candle_features | best_ask |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | best_bid |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | bid_top_qty |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | book_event_count |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | book_is_stale |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | book_staleness_ms |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | buy_base_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 0.0 \|\| 4.58118 \|\| 10.61649 | sample |
| quants_lab | candle_features | buy_quote_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 0.0 \|\| 10775.4851016 \|\| 25007.7391388 | sample |
| quants_lab | candle_features | buy_trade_count |  | 0 | 5000 | 5000 | 1.0 | True | int | 0 \|\| 1 \|\| 4 | sample |
| quants_lab | candle_features | close_ts |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716280 \|\| 1773716220 \|\| 1773716160 | sample |
| quants_lab | candle_features | connector |  | 0 | 5000 | 5000 | 1.0 | True | string | "nonkyc" \|\| "mexc" | sample |
| quants_lab | candle_features | features_partially_missing |  | 0 | 5000 | 5000 | 1.0 | True | bool | false | sample |
| quants_lab | candle_features | imbalance_top1 |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | imbalance_top5 |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | ingested_at |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716332 \|\| 1773716362 \|\| 1773716422 | sample |
| quants_lab | candle_features | interval |  | 0 | 5000 | 5000 | 1.0 | True | string | "1m" \|\| "5m" | sample |
| quants_lab | candle_features | is_closed |  | 0 | 5000 | 5000 | 1.0 | True | bool | true | sample |
| quants_lab | candle_features | is_synthetic |  | 0 | 5000 | 5000 | 1.0 | True | bool | false | sample |
| quants_lab | candle_features | max_trade_size_base |  | 0 | 5000 | 5000 | 1.0 | True | double | 5.37018 \|\| 4.58118 \|\| 5.54756 | sample |
| quants_lab | candle_features | max_trade_size_quote |  | 0 | 5000 | 5000 | 1.0 | True | double | 12633.0262392 \|\| 10775.4851016 \|\| 13068.387091999999 | sample |
| quants_lab | candle_features | microprice |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | mid_price |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | no_trade_interval |  | 0 | 5000 | 5000 | 1.0 | True | bool | false | sample |
| quants_lab | candle_features | open_ts |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716220 \|\| 1773716160 \|\| 1773716100 | sample |
| quants_lab | candle_features | qc_flags |  | 0 | 5000 | 5000 | 1.0 | True | array | [] | sample |
| quants_lab | candle_features | quote_asset |  | 0 | 5000 | 5000 | 1.0 | True | string | "USDT" \|\| "XMR" \|\| "BTC" | sample |
| quants_lab | candle_features | schema_version |  | 0 | 5000 | 5000 | 1.0 | True | int | 1 | sample |
| quants_lab | candle_features | sell_base_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 13.35521 \|\| 3.48743 \|\| 4.3369 | sample |
| quants_lab | candle_features | sell_quote_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 31417.1939007 \|\| 8199.436170199999 \|\| 10223.374370000001 | sample |
| quants_lab | candle_features | sell_trade_count |  | 0 | 5000 | 5000 | 1.0 | True | int | 4 \|\| 1 \|\| 5 | sample |
| quants_lab | candle_features | signed_base_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | -13.35521 \|\| 1.09375 \|\| 6.27959 | sample |
| quants_lab | candle_features | signed_quote_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | -31417.1939007 \|\| 2576.048931400001 \|\| 14784.364768799998 | sample |
| quants_lab | candle_features | source_flags |  | 0 | 5000 | 5000 | 1.0 | True | array | [] | sample |
| quants_lab | candle_features | spread_abs |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | spread_bps |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | timestamp |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716220 \|\| 1773716160 \|\| 1773716100 | sample |
| quants_lab | candle_features | top5_ask_qty |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | top5_bid_qty |  | 0 | 5000 | 5000 | 1.0 | True | null | null | sample |
| quants_lab | candle_features | trade_count |  | 0 | 5000 | 5000 | 1.0 | True | int | 4 \|\| 2 \|\| 5 | sample |
| quants_lab | candle_features | trade_imbalance_ratio |  | 0 | 5000 | 5000 | 1.0 | True | double | -1.0 \|\| 0.0 \|\| 0.6 | sample |
| quants_lab | candle_features | trade_vwap |  | 0 | 5000 | 5000 | 1.0 | True | double | 2352.42979336903 \|\| 2351.696422531266 \|\| 2356.061970482947 | sample |
| quants_lab | candle_features | trading_pair |  | 0 | 5000 | 5000 | 1.0 | True | string | "ETH-USDT" \|\| "XNV-XMR" \|\| "GHOST-XMR" | sample |
| quants_lab | candle_features | updated_at |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773717071 \|\| 1773716332 \|\| 1773731272 | sample |
| quants_lab | candle_features | volume_imbalance_ratio |  | 0 | 5000 | 5000 | 1.0 | True | double | -1.0 \|\| 0.13555619 \|\| 0.41994424 | sample |
| quants_lab | candles | _id |  | 0 | 5000 | 5000 | 1.0 | True | objectId | {"$oid": "69a6081c3963f2b299061764"} \|\| {"$oid": "69a6081c3963f2b299061765"} \|\| {"$oid": "69a6081c3963f2b299061766"} | sample |
| quants_lab | candles | base_asset |  | 0 | 5000 | 5000 | 1.0 | True | string | "BTC" | sample |
| quants_lab | candles | base_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 0.443 \|\| 1.285 \|\| 1.79 | sample |
| quants_lab | candles | close |  | 0 | 5000 | 5000 | 1.0 | True | double | 67312.49 \|\| 67191.21 \|\| 67238.38 | sample |
| quants_lab | candles | close_ts |  | 0 | 5000 | 5000 | 1.0 | True | int | 1772338500 \|\| 1772338800 \|\| 1772339100 | sample |
| quants_lab | candles | connector |  | 0 | 5000 | 5000 | 1.0 | True | string | "nonkyc" | sample |
| quants_lab | candles | high |  | 0 | 5000 | 5000 | 1.0 | True | double | 67408.39 \|\| 67326.31 \|\| 67287.0 | sample |
| quants_lab | candles | ingested_at |  | 0 | 5000 | 5000 | 1.0 | True | int | 1772953582 | sample |
| quants_lab | candles | interval |  | 0 | 5000 | 5000 | 1.0 | True | string | "5m" | sample |
| quants_lab | candles | is_closed |  | 0 | 5000 | 5000 | 1.0 | True | bool | true | sample |
| quants_lab | candles | low |  | 0 | 5000 | 5000 | 1.0 | True | double | 67225.44 \|\| 67081.45 \|\| 67191.78 | sample |
| quants_lab | candles | open |  | 0 | 5000 | 5000 | 1.0 | True | double | 67368.44 \|\| 67276.85 \|\| 67211.42 | sample |
| quants_lab | candles | open_ts |  | 0 | 5000 | 5000 | 1.0 | True | int | 1772338200 \|\| 1772338500 \|\| 1772338800 | sample |
| quants_lab | candles | qc_flags |  | 0 | 5000 | 5000 | 1.0 | True | array | [] | sample |
| quants_lab | candles | qc_ok |  | 0 | 5000 | 5000 | 1.0 | True | bool | true | sample |
| quants_lab | candles | quote_asset |  | 0 | 5000 | 5000 | 1.0 | True | string | "USDT" | sample |
| quants_lab | candles | quote_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 29820.73992 \|\| 86351.55881666667 \|\| 120357.90546666666 | sample |
| quants_lab | candles | quote_volume_is_estimated |  | 0 | 5000 | 5000 | 1.0 | True | bool | true | sample |
| quants_lab | candles | schema_version |  | 0 | 5000 | 5000 | 1.0 | True | int | 3 | sample |
| quants_lab | candles | timestamp |  | 0 | 5000 | 5000 | 1.0 | True | int | 1772338200 \|\| 1772338500 \|\| 1772338800 | sample |
| quants_lab | candles | trading_pair |  | 0 | 5000 | 5000 | 1.0 | True | string | "BTC-USDT" | sample |
| quants_lab | candles | updated_at |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716190 | sample |
| quants_lab | candles | volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 0.443 \|\| 1.285 \|\| 1.79 | sample |
| quants_lab | market_trades | _id |  | 0 | 5000 | 5000 | 1.0 | True | objectId | {"$oid": "69b8c352f7f2f0931fa01cd2"} \|\| {"$oid": "69b8c352f7f2f0931fa01cd3"} \|\| {"$oid": "69b8c352f7f2f0931fa01cd4"} | sample |
| quants_lab | market_trades | base_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 4.53327 \|\| 4.61058 \|\| 2.30689 | sample |
| quants_lab | market_trades | connector |  | 0 | 5000 | 5000 | 1.0 | True | string | "nonkyc" \|\| "mexc" | sample |
| quants_lab | market_trades | ingested_at |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716306 \|\| 1773716307 \|\| 1773716311 | sample |
| quants_lab | market_trades | is_buyer_maker |  | 0 | 5000 | 2405 | 0.481 | False | bool | true \|\| false | sample |
| quants_lab | market_trades | price |  | 0 | 5000 | 5000 | 1.0 | True | double | 2352.06 \|\| 2352.32 \|\| 2352.63 | sample |
| quants_lab | market_trades | quote_volume |  | 0 | 5000 | 5000 | 1.0 | True | double | 10662.5230362 \|\| 10845.5595456 \|\| 5427.2586207 | sample |
| quants_lab | market_trades | raw |  | 0 | 5000 | 2405 | 0.481 | False | object | {"id": null, "price": "75061.61", "qty": "0.00004011", "quoteQty": "3.0107211771", "time": 1773717148409, "isBuyerMaker": true, "isBestMatch": true, "tradeType": "ASK"} \|\| {"id": null, "price": "75061.61", "qty": "0.00026562", "quoteQty": "19.9378648482", "time": 1773717148355, "isBuyerMaker": true, "isBestMatch": true, "tradeType": "ASK"} \|\| {"id": null, "price": "75061.61", "qty": "0.0002656", "quoteQty": "19.936363616", "time": 1773717148290, "isBuyerMaker": true, "isBestMatch": true, "tradeType": "ASK"} | sample |
| quants_lab | market_trades | raw.id | raw | 1 | 5000 | 2405 | 0.481 | False | null | null | sample |
| quants_lab | market_trades | raw.isBestMatch | raw | 1 | 5000 | 2405 | 0.481 | False | bool | true | sample |
| quants_lab | market_trades | raw.isBuyerMaker | raw | 1 | 5000 | 2405 | 0.481 | False | bool | true \|\| false | sample |
| quants_lab | market_trades | raw.price | raw | 1 | 5000 | 2405 | 0.481 | False | string | "75061.61" \|\| "75054.64" \|\| "75053.14" | sample |
| quants_lab | market_trades | raw.qty | raw | 1 | 5000 | 2405 | 0.481 | False | string | "0.00004011" \|\| "0.00026562" \|\| "0.0002656" | sample |
| quants_lab | market_trades | raw.quoteQty | raw | 1 | 5000 | 2405 | 0.481 | False | string | "3.0107211771" \|\| "19.9378648482" \|\| "19.936363616" | sample |
| quants_lab | market_trades | raw.time | raw | 1 | 5000 | 2405 | 0.481 | False | int | 1773717148409 \|\| 1773717148355 \|\| 1773717148290 | sample |
| quants_lab | market_trades | raw.tradeType | raw | 1 | 5000 | 2405 | 0.481 | False | string | "ASK" \|\| "BID" | sample |
| quants_lab | market_trades | schema_version |  | 0 | 5000 | 5000 | 1.0 | True | int | 2 | sample |
| quants_lab | market_trades | side |  | 0 | 5000 | 5000 | 1.0 | True | string | "buy" \|\| "sell" | sample |
| quants_lab | market_trades | source |  | 0 | 5000 | 5000 | 1.0 | True | string | "ws_trades" \|\| "rest_trades" | sample |
| quants_lab | market_trades | timestamp |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716285 \|\| 1773716269 \|\| 1773716255 | sample |
| quants_lab | market_trades | timestampms |  | 0 | 5000 | 5000 | 1.0 | True | int | 1773716285432 \|\| 1773716269402 \|\| 1773716255363 | sample |
| quants_lab | market_trades | trade_id |  | 0 | 5000 | 5000 | 1.0 | True | string | "ws_69b8c33d4d4d4223aac536a9" \|\| "ws_69b8c32d4d4d4223aac52701" \|\| "ws_69b8c31f4d4d4223aac51b65" | sample |
| quants_lab | market_trades | trading_pair |  | 0 | 5000 | 5000 | 1.0 | True | string | "ETH-USDT" \|\| "XNV-XMR" \|\| "GHOST-XMR" | sample |
| quants_lab | symbol_metadata | _id |  | 0 | 33 | 33 | 1.0 | True | objectId | {"$oid": "69b8c34cf7f2f0931fa01a84"} \|\| {"$oid": "69b8c34cf7f2f0931fa01a85"} \|\| {"$oid": "69b8c34cf7f2f0931fa01a86"} | full |
| quants_lab | symbol_metadata | base_asset |  | 0 | 33 | 33 | 1.0 | True | string | "BTC" \|\| "ETH" \|\| "SOL" | full |
| quants_lab | symbol_metadata | connector |  | 0 | 33 | 33 | 1.0 | True | string | "nonkyc" \|\| "mexc" | full |
| quants_lab | symbol_metadata | maker_fee |  | 0 | 33 | 33 | 1.0 | True | null | null | full |
| quants_lab | symbol_metadata | min_notional |  | 0 | 33 | 33 | 1.0 | True | null | null | full |
| quants_lab | symbol_metadata | min_order_qty |  | 0 | 33 | 33 | 1.0 | True | null | null | full |
| quants_lab | symbol_metadata | permissions |  | 0 | 33 | 12 | 0.363636 | False | array | ["SPOT"] | full |
| quants_lab | symbol_metadata | permissions[] | permissions | 1 | 33 | 12 | 0.363636 | False | string | "SPOT" | full |
| quants_lab | symbol_metadata | price_decimals |  | 0 | 33 | 33 | 1.0 | True | int\|null | 8 \|\| null | full |
| quants_lab | symbol_metadata | quantity_decimals |  | 0 | 33 | 33 | 1.0 | True | int\|null | 8 \|\| null | full |
| quants_lab | symbol_metadata | quantity_step |  | 0 | 33 | 33 | 1.0 | True | double\|null | 1e-08 \|\| null | full |
| quants_lab | symbol_metadata | quote_asset |  | 0 | 33 | 33 | 1.0 | True | string | "USDT" \|\| "XMR" \|\| "BTC" | full |
| quants_lab | symbol_metadata | schema_version |  | 0 | 33 | 33 | 1.0 | True | int | 1 | full |
| quants_lab | symbol_metadata | source |  | 0 | 33 | 33 | 1.0 | True | string | "market_info" \|\| "exchangeInfo" | full |
| quants_lab | symbol_metadata | status |  | 0 | 33 | 33 | 1.0 | True | string | "ACTIVE" \|\| "1" | full |
| quants_lab | symbol_metadata | taker_fee |  | 0 | 33 | 33 | 1.0 | True | null | null | full |
| quants_lab | symbol_metadata | tick_size |  | 0 | 33 | 33 | 1.0 | True | double\|null | 1e-08 \|\| null | full |
| quants_lab | symbol_metadata | trading_pair |  | 0 | 33 | 33 | 1.0 | True | string | "BTC-USDT" \|\| "ETH-USDT" \|\| "SOL-USDT" | full |
| quants_lab | symbol_metadata | updated_at |  | 0 | 33 | 33 | 1.0 | True | int | 1773783822 \|\| 1773783823 \|\| 1773783824 | full |