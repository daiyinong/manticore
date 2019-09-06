
contract Test {
    event Log(string);

    function target(int a, int b) payable public {
        if (a > 10 && b < 5)
            emit Log("yes");
        else
            emit Log("no");

    } 

}
