# Test Client - TestClient - FastAPI

## Metadata

- **URL**: [https://fastapi.tiangolo.com/reference/testclient/](https://fastapi.tiangolo.com/reference/testclient/)
- **Crawled**: 2025-10-04T23:49:06.537315
- **Depth**: 1
- **Status**: 200
- **Load Time**: 0.09s
- **Word Count**: 966

**Description**: FastAPI framework, high performance, easy to learn, fast to code, ready for production

---

## Content

Test Client - TestClient
¶
You can use the TestClient
class to test FastAPI applications without creating an actual HTTP and socket connection, just communicating directly with the FastAPI code.
Read more about it in the FastAPI docs for Testing.
You can import it directly from fastapi.testclient
:
from fastapi.testclient import TestClient
fastapi.testclient.TestClient
¶
TestClient(
app,
base_url="http://testserver",
raise_server_exceptions=True,
root_path="",
backend="asyncio",
backend_options=None,
cookies=None,
headers=None,
follow_redirects=True,
client=("testclient", 50000),
)
Bases: Client
Source code in starlette/testclient.py
379 380 381 382 383 384 385 386 387 388 389 390 391 392 393 394 395 396 397 398 399 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 |
|
auth
property
writable
¶
auth
Authentication class used when none is passed at the request-level.
See also Authentication.
async_backend
instance-attribute
¶
async_backend = _AsyncBackend(
backend=backend, backend_options=backend_options or {}
)
build_request
¶
build_request(
method,
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Build and return a request instance.
- The
params
,headers
andcookies
arguments are merged with any values set on the client. - The
url
argument is merged with anybase_url
set on the client.
See also: Request instances
Source code in httpx/_client.py
340 341 342 343 344 345 346 347 348 349 350 351 352 353 354 355 356 357 358 359 360 361 362 363 364 365 366 367 368 369 370 371 372 373 374 375 376 377 378 379 380 381 382 383 384 385 386 387 388 389 |
|
stream
¶
stream(
method,
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Alternative to httpx.request()
that streams the response body
instead of loading it into memory at once.
Parameters: See httpx.request
.
See also: Streaming Responses
Source code in httpx/_client.py
827 828 829 830 831 832 833 834 835 836 837 838 839 840 841 842 843 844 845 846 847 848 849 850 851 852 853 854 855 856 857 858 859 860 861 862 863 864 865 866 867 868 869 870 871 872 873 874 875 876 877 |
|
send
¶
send(
request,
*,
stream=False,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT
)
Send a request.
The request is sent as-is, unmodified.
Typically you'll want to build one with Client.build_request()
so that any client-level configuration is merged into the request,
but passing an explicit httpx.Request()
is supported as well.
See also: Request instances
Source code in httpx/_client.py
879 880 881 882 883 884 885 886 887 888 889 890 891 892 893 894 895 896 897 898 899 900 901 902 903 904 905 906 907 908 909 910 911 912 913 914 915 916 917 918 919 920 921 922 923 924 925 926 927 928 |
|
close
¶
close()
Close transport and proxies.
Source code in httpx/_client.py
1263 1264 1265 1266 1267 1268 1269 1270 1271 1272 1273 |
|
request
¶
request(
method,
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
427 428 429 430 431 432 433 434 435 436 437 438 439 440 441 442 443 444 445 446 447 448 449 450 451 452 453 454 455 456 457 458 459 460 461 462 463 464 465 |
|
get
¶
get(
url,
*,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
467 468 469 470 471 472 473 474 475 476 477 478 479 480 481 482 483 484 485 486 487 488 |
|
options
¶
options(
url,
*,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
490 491 492 493 494 495 496 497 498 499 500 501 502 503 504 505 506 507 508 509 510 511 |
|
head
¶
head(
url,
*,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
513 514 515 516 517 518 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 |
|
post
¶
post(
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
536 537 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555 556 557 558 559 560 561 562 563 564 565 |
|
put
¶
put(
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
567 568 569 570 571 572 573 574 575 576 577 578 579 580 581 582 583 584 585 586 587 588 589 590 591 592 593 594 595 596 |
|
patch
¶
patch(
url,
*,
content=None,
data=None,
files=None,
json=None,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
598 599 600 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 627 |
|
delete
¶
delete(
url,
*,
params=None,
headers=None,
cookies=None,
auth=USE_CLIENT_DEFAULT,
follow_redirects=USE_CLIENT_DEFAULT,
timeout=USE_CLIENT_DEFAULT,
extensions=None
)
Source code in starlette/testclient.py
629 630 631 632 633 634 635 636 637 638 639 640 641 642 643 644 645 646 647 648 649 650 |
|
websocket_connect
¶
websocket_connect(url, subprotocols=None, **kwargs)
Source code in starlette/testclient.py
652 653 654 655 656 657 658 659 660 661 662 663 664 665 666 667 668 669 670 671 672 673 |
|
lifespan
async
¶
lifespan()
Source code in starlette/testclient.py
707 708 709 710 711 712 |
|
wait_startup
async
¶
wait_startup()
Source code in starlette/testclient.py
714 715 716 717 718 719 720 721 722 723 724 725 726 727 728 729 |
|
wait_shutdown
async
¶
wait_shutdown()
Source code in starlette/testclient.py
731 732 733 734 735 736 737 738 739 740 741 742 743 744 745 |
|