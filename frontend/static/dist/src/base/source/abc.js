'use strict';

const e = React.createElement;

class Abc extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return this.props.text;
    }
}

export default Abc;